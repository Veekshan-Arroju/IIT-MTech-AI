#!/bin/bash
set -euxo pipefail

apt-get update
apt-get install -y apache2

HOSTNAME=$(hostname)
cat > /var/www/html/index.html <<EOF
<html>
  <head><title>VCC Auto-Scaling Demo</title></head>
  <body>
    <h1>It works!</h1>
    <p>Served by: <b>${HOSTNAME}</b></p>
    <p>Time: <b>$(date -u)</b> UTC</p>
  </body>
</html>
EOF

systemctl enable apache2
systemctl restart apache2
