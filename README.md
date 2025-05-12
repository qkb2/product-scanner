# Product Scanner
This system consists of:
1. main server with its frontend, with a database of products for scanning and weight verification
2. edge servers with their frontends connecting to the main server, set up on RPi with a camera and with a HX711 controlled gauge for weight measurement.

Multiple edge servers can connect to main server, which stores their names and API keys. Main server verifies the products by means of ResNet18, but can be manually retrained with transfer learning (requires updating indices in the database, if set up incorrectly).

System uses a common passphrase for authentication and authorization. All privileges to dirs in-project should thus be set to minimum. Project is not production-ready and is only a simple demo.