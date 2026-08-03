curl -fsSL -o /tmp/gvm-installer https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer
bash /tmp/gvm-installer
source /root/.gvm/scripts/gvm
gvm version
apt install -y curl git mercurial make binutils bison gcc build-essential