### NWERC bets
---
Place named files with bets in the `bets` subdirectory and run the `bet.py` script.
The API URL most likely is `<domjudge-url>/api/v4/` (including the `/` at the end).

https://hpi.de/friedrich/judge/api/v4/

Post the resulting hash in the jury chat, but do not push your actual bets to the repo before the contest starts!

The bets represent the expected percentage of teams that does NOT solve the problem:
- 0 = easiest problem, every team solves
- 100 = hardest problem, no team solves

`bets/example.txt`:
```
A 100.0
B 30.4
C 37.7
D 42.0
E 57.2
F 100.0
G 73.9
H 69.6
I 5.8
J 71.7
K 91.3
L 97.8
```

### Offline install
---
Run the following command on a device with internet connection:
```pip download -r requirements.txt```

On the target device run:
```
pip install --no-index --find-links /path/to/download/dir/ -r requirements.txt
```

For Debian/Ubuntu, if the target device does not have `pip`, run `apt-get download python3-wheel python3-pip` on the source device, then `dpkg -i <package-names>` on the target device.
