# system-config-samba-focal

Alternative debian package of system-config-samba fixed to focal

## How to install

```bash
wget -qO - "https://winunix.github.io/debian/public.key" | sudo apt-key add -
echo "deb https://winunix.github.io/debian focal main" | sudo tee /etc/apt/sources.list.d/winunix-focal.list
sudo apt update
sudo apt install system-config-samba-focal
```
