// Wrapper program to make testlib interactors work under DOMjudge.
//
// The main problem solved by this wrapper is, that an interactor needs to
// consume all output of a solution before it may finish. This wrapper
// forwards all solution output to the interactor, and simply discards
// additional input if the interactor finishes before the solution.
//
// It also hands through the exit code of the interactor which determines the
// solutions verdict.
//
// See docs/interactors.md for the full overview of how interactors work.

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>


// We use the same error code as our custom version of testlib.h
constexpr int EXIT_ERROR = 44;

int pipe_read, pipe_write;
pid_t pid;

[[noreturn]] void exit_safely(bool error) {
    // The last thing we want to do is leave a zombie process, since that
    // sends the judgehost into a restart loop. Thus we always wait for
    // the child process to finish, ignoring some of the errors from the
    // syscalls we make in this function.

    // Close the write end of the pipe to signal the child process to exit,
    // if it is still running
    if (close(pipe_write)) {
        perror("close");
    }

    // If there was an error, suggest the child process a bit harder that
    // it should exit
    if (error) {
        if (kill(pid, SIGTERM)) {
            perror("kill");
        }
    }

    // Wait for the child process to finish, if it hasn't already
    while (1) {
        int stats;
        if (waitpid(pid, &stats, 0) == -1) {
            if (errno != EINTR) {
                // We should not get here, but just in case
                perror("wait");
                exit(EXIT_ERROR);
            }
        } else {
            exit(WEXITSTATUS(stats));
        }
    }
}

void exit_error(const char* syscall) {
    perror(syscall);
    exit_safely(true);
}

int main(int argc, char* argv[]) {
    // Create a pipe to connect to child process
    int filedes[2];
    if (pipe(filedes)) {
        perror("pipe");
        exit(EXIT_ERROR);
    }

    pipe_read = filedes[0];
    pipe_write = filedes[1];

    // Spawn child process and set the pipes read end as its stdin
    if ((pid = fork()) == -1) {
        perror("fork");
        exit(EXIT_ERROR);
    } else if (pid == 0) {
        // Connect stdin to the read end of the pipe, and close unnecessary filenos
        if (close(pipe_write)) {
            perror("close");
            _exit(EXIT_ERROR);
        }
        if (dup2(pipe_read, STDIN_FILENO) == -1) {
            perror("dup2");
            _exit(EXIT_ERROR);
        }
        if (close(pipe_read)) {
            perror("close");
            _exit(EXIT_ERROR);
        }
        execvp(argv[1], &argv[1]);
        perror("execvp");
        _exit(EXIT_ERROR);
    }

    if (close(pipe_read)) {
        exit_error("close");
    }

    // Block SIGPIPE so that we get notified when the child process has closed
    // its stdin, in which case we will discard the remaining input
    if (signal(SIGPIPE, SIG_IGN) == SIG_ERR) {
        exit_error("signal");
    }

    constexpr int BUFSIZE = 4096;
    char buffer[BUFSIZE];
    bool pipe_closed = false;
    while (1) {
        // Read from stdin, repeating if interrupted
        ssize_t num_read;
        while (1) {
            num_read = read(STDIN_FILENO, buffer, BUFSIZE);
            if (num_read == -1) {
                if (errno != EINTR) {
                    exit_error("read");
                }
            } else {
                break;
            }
        }

        // Break on EOF
        if (num_read == 0) {
            break;
        }

        // When the child process finished, we simply discard any further data
        if (pipe_closed) {
            continue;
        }

        // Write to child process, repeating if interrupted
        // An EPIPE error signals that the read end oof the pipe is closed,
        // which means that we can start discarding input.
        ssize_t num_written = 0;
        while (num_written < num_read) {
            ssize_t written = write(pipe_write, &buffer[num_written], num_read - num_written);
            if (written == -1) {
                if (errno == EPIPE) {
                    pipe_closed = true;
                    break;
                } else if (errno != EINTR) {
                    exit_error("write");
                }
            } else {
                num_written += written;
            }
        }
    }

    exit_safely(false);
}
