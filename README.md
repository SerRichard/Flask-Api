# **Flask Api for c02-Intesity**

With user registration, token authentication, and microservicing

## Installation and preparation: Linux users

To install the requirements for running the app.

```
pip3 install -r requrements.txt
```

Then set up your CQL database

```
sudo docker pull cassandra:latest
sudo docker run --name c02-docker -p 9042:9042 -d cassandra:latest
sudo docker cp c02.csv c02-docker:/home/c02.csv
```
After setting up the cassanda docker, go ahead and run the database
```
sudo docker exec -it c02-docker cqlsh
```
Now create the keyspace and table to store the API's data

```
>CREATE KEYSPACE c02 WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor' : 1};
>CREATE TABLE c02.stats (regionid int, name text, postcode text PRIMARY KEY, forecast text, indx text, Date text);
```
Returning to terminal, it is important to ensure the python code will try to connect to the correct location.
Open the c02_api.py
```
sudo nano c02_api.py
```
Modify the IP address in the following line, to your own IP address.
```
cluster = Cluster(contact_points=['54.167.248.218'],port=9042)
```
*Ctrl+C and save changes*

Now we have the requirements installed and the database set up, the server is ready to run

## Running

Run the server
```
sudo python3 c02_api.py
```
From a different window requests can be sent.

## API Documentation

-**POST** /register 

Register a new user.
The request must contain a JSON object that defines username and password.
If succesful, a 201 is returned along with the new user's username.
If unsuccessful, a 400 will be returned for either no username or password value
being submitted, or if the username already exists.

-**GET** /token

Use user information to get a token for accession protected app.route's.
The request must contain the username and password.
If unsuccessful, a 400 will be returned on default.
If successful, 200 is returned along with the generated token.
This token is unique and will be valid for a 30 minute period. Must be
supplied when accessing protect routes.

-**GET (external)** /<postcode>

Submit a curl GET request and the route shall be the first section of a standard UK postcode.
This request tells the API to access an external API and get latest c02 intestity for the postcode.
If sucessful, a 200 is returned with the data from the external API.

-**GET (internal)** /postcode

Get data entries for 
This request will pull all of the enteries for different postcodes that are in my API database,
and return them.

**POST** /postcode

Post a new postcode. Protected with authentication. Requires token.
This request posts a new entry to the API, and commits it to the database.

**PUT** /postcode

Update a postcode entry in the database. Protected with authentication. Requires token.
This request allows the user to update an entry in API. Update forecast, indx and date.

**DELETE** /postcode

Remove a postcode entry from the database. This may be done if duplicate entries are found.
This request is protected with authenticion and requires a token. Only takes one entry
(the postcode) in the JSON object.

## Examples

Example register:
```
curl -i -H "Content-Type: application/json" -X POST -d '{"username":"sean","password":"student"}' ec2-35-171-189-126.compute-1.amazonaws.com/register
```

Example get token:
```
curl -u sean:student -i -X GET ec2-35-171-189-126.compute-1.amazonaws.com/token
```

Example external get:
```
curl -i ec2-35-171-189-126.compute-1.amazonaws.com/E1
```

Example internal get:
```
curl -i ec2-35-171-189-126.compute-1.amazonaws.com/postcode
```

Example post entry:
```
curl -i -H "Content-Type:application/json" -X POST -d '{"regionid":13,"name":"South East","postcode":"ME16","forecast":"215","indx":"moderate","date":"24-03-2020"}' --user eyJhbGciOiJIUzUxMiIsImV4cCI6MTU4NjUzMTczOCwiaWF0IjoxNTg2NTMxMTM4fQ.eyJpZCI6Mn0._8NNVOfxgnkcKorjv3x48NUnYqZucuJTEzS6FXcknTsDYcGJlge9QBzIsKOAZPCtBRVOQSVz7QEiQ9rBknP2Ug:x c2-35-171-189-126.compute-1.amazonaws.com/postcode
```

Example put (update) entry:
```
curl -i -H "Content-Type:application/json" -X PUT -d '{"postcode":"ME16","forecast":"458","indx":"High","date":"10-04-2020"}' --user eyJhbGciOiJIUzUxMiIsImV4cCI6MTU4NjUzMTczOCwiaWF0IjoxNTg2NTMxMTM4fQ.eyJpZCI6Mn0._8NNVOfxgnkcKorjv3x48NUnYqZucuJTEzS6FXcknTsDYcGJlge9QBzIsKOAZPCtBRVOQSVz7QEiQ9rBknP2Ug:x c2-35-171-189-126.compute-1.amazonaws.com/postcode
```

Example delete entry:
```
curl -i -H "Content-Type:application/json" -X DELETE -d '{"postcode":"E1"}' --user eyJhbGciOiJIUzUxMiIsImV4cCI6MTU4NjUzMjQyNywiaWF0IjoxNTg2NTMxODI3fQ.eyJpZCI6Mn0.wEWtd3zSZb7efogusUE3JS2qmwW2PB0VbetcNb7jJOTqYo30RZXX7hL_7-dw2JODcG9z7zYNrdT3NUh6izIrEA:x c2-35-171-189-126.compute-1.amazonaws.com/postcode
```
