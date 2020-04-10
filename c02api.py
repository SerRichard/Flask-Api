
from flask import Flask, request, jsonify
import json
import requests
import requests_cache
from pprint import pprint

with open('c02_db.json') as f:
  all_codes = json.load(f)

app = Flask(__name__)

@app.route('/allpostcodes', methods=['GET'])
def get_all_postcodes():
        return jsonify(all_codes)

@app.route('/<postcode>', methods=['GET'])
def external_postcode(postcode):
	#postcode = request.json['postcode']
	c02_postcode_template = 'https://api.carbonintensity.org.uk/regional/postcode/{pstcd}'
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if resp.ok:
		c02 = resp.json()
		return jsonify(c02)
	else:
		print(resp.reason)

@app.route('/postcode', methods=['POST'])
def add_a_postcode():
	postcode = request.json['postcode']
	c02_postcode_template = 'https://api.carbonintensity.org.uk/regional/postcode/{pstcd}'
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if resp.ok:
		c02 = resp.json()
		all_codes.append(c02)
		return jsonify(c02)
	else:
		print(resp.reason)

@app.route('/<postcode>', methods=['DELETE'])
def remove_matching_postcode(postcode):
#	code = request.json['postcode']
#	data = jsonify(all_codes)
	value = [y for x in all_codes for y in x if x['postcode'] == postcode]


	return jsonify(value)
	#	if request.json['postcode'] in all_codes:
	#	else:
		#return jsonify({'Nope':'no match found'}), 404

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)

