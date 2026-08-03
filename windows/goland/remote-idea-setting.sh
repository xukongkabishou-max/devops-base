mkdir -p /data/csk/goland_idea/{cache,config,data,tmp}
cat >> ~/.profile <<'EOF'

# GoLand Remote Development storage
export XDG_CACHE_HOME=/data/csk/goland_idea/cache
export XDG_CONFIG_HOME=/data/csk/goland_idea/config
export XDG_DATA_HOME=/data/csk/goland_idea/data
export TMPDIR=/data/csk/goland_idea/tmp
EOF

cat >> ~/.bashrc <<'EOF'

# GoLand Remote Development storage
export XDG_CACHE_HOME=/data/csk/goland_idea/cache
export XDG_CONFIG_HOME=/data/csk/goland_idea/config
export XDG_DATA_HOME=/data/csk/goland_idea/data
export TMPDIR=/data/csk/goland_idea/tmp
EOF

source ~/.profile
source ~/.bashrc