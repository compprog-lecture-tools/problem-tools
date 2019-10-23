# Setting up a local judge system

This describes how to setup a local judge system for the purpose of developing problems.
For this you will need Docker and Docker Compose, as well as about a little over 3GB of disk space for the docker images.
On Linux you will also have to enable cgroups (usually already active) and enable memory limits imposed by them (see [this](https://askubuntu.com/a/417221) for how, it should be applicable for any system using Grub).

To start, run `docker-compose up -d` in this directory.
This will download the docker images and then start them in the background.
You follow the startup process using `docker-compose logs -f`.
Don't worry if the `judge-web` container is restarting repeatedly, it will do that until the database is reachable.

Once the web interface is reachable at [http://localhost:8080/](http://localhost:8080/), run the `./setup-dev-settings.sh` script.
If you are on Windows and don't have WSL or a Bash setup, just run the commands from the script manually, there is only two of them.
This will setup an account named `test` with password `test` for you, that can both submit solutions as well as access anything on the internal side of things.
It also creates a testing contest running indefinitely, and sets many settings you are used to from the main judge.

To shutdown the judge, run `docker-compose down` in this directory.

## Cleaning up

If you don't need the local setup anymore, you can reclaim disk space by deleting the docker images used for the judge.
To list installed docker images run `docker image ls`, and delete them using `docker image rm`.
You probably also want to delete the docker volume containing the database.
Find it with `docker volume ls` (it should be named `local-judge_judge-db`) and delete it with `docker volume rm`.
