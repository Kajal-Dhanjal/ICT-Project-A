const https = require('https');
const fs = require('fs');
const path = require('path');

// Load TLS certificate and key
const options = {
  key: fs.readFileSync(path.join(__dirname, 'cert', 'key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'cert', 'cert.pem'))
};

https.createServer(options, (req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html' });
  fs.createReadStream('index.html').pipe(res);
}).listen(4430, () => {
  console.log('Server running at https://localhost:4430/');
});
