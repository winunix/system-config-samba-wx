# system-config-samba for Jammy, Focal and Bionic

Alternative debian package of system-config-samba fixed to jammy, focal and bionic

## How to install on Jammy (Ubuntu 22.04)

```bash
wget -qO - "https://winunix.github.io/debs/winunix.asc" | sudo tee /etc/apt/trusted.gpg.d/winunix.asc
echo "deb https://winunix.github.io/debs jammy main" | sudo tee /etc/apt/sources.list.d/winunix-jammy.list
sudo apt update
sudo apt install system-config-samba-wx
```


## How to install on Focal or Bionic (Ubuntu 20.04 or 18.04)

```bash
wget -qO - "https://winunix.github.io/debian/public.key" | sudo apt-key add -
echo "deb https://winunix.github.io/debian focal main" | sudo tee /etc/apt/sources.list.d/winunix-focal.list
sudo apt update
sudo apt install system-config-samba-wx
```
