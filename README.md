# system-config-samba for Focal and Bionic

Alternative debian package of system-config-samba fixed to focal and bionic

## How to install

```bash
wget -qO - "https://winunix.github.io/debian/public.key" | sudo apt-key add -
echo "deb https://winunix.github.io/debian focal main" | sudo tee /etc/apt/sources.list.d/winunix-focal.list
sudo apt update
sudo apt install system-config-samba-wx
```
