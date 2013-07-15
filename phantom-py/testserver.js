// HTTP Server
// Allows us to ping service on local tunnel
var http = require('http'); 
var web = http.createServer(function(request, response) { 
  response.writeHead(200, { 
    'Content-Type': 'text/plain' 
  }); 
  response.end('Tapirs are beautiful!\n'); 
}); 
web.listen(4001);