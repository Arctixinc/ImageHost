from flask import Flask, request, Response, jsonify
import requests
from bs4 import BeautifulSoup
import secrets
from io import BytesIO

app = Flask(__name__)

class PostImagesUploader:
    @staticmethod
    def upload_image_to_postimg(image_file, image_name):
        try:
            # Generate a session ID
            session_id = secrets.randbits(64)
            image_extension = image_name.split(".")[-1]

            # Prepare the URL and payload
            url = "https://postimages.org/json/rr"
            payload = {
                'optsize': '0',
                'expire': '0',
                'numfiles': '1',
                'upload_session': session_id,
                'gallery': ''
            }

            # Prepare files
            files = {
                'file': (image_name, image_file, f'image/{image_extension}')
            }

            # Prepare headers
            headers = {
                'Cache-Control': 'no-cache',
                'Referer': 'https://postimages.org/',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }

            # Make the POST request
            response = requests.post(url, headers=headers, data=payload, files=files)
            response_json = response.json()

            # Fetch the indirect URL
            indirect_url = response_json.get("url")
            if not indirect_url:
                raise Exception("Failed to retrieve upload URL.")

            # Fetch the source code of the indirect URL
            source_code = requests.get(indirect_url).text
            soup = BeautifulSoup(source_code, "html.parser")

            # Find and return the direct link
            direct_link = soup.find("input", {"id": "code_direct"})["value"]
            return direct_link

        except Exception as e:
            print("Error:", e)
            return None

@app.route('/', methods=['POST'])
def upload_image():
    try:
        # Check if an image file is provided
        if 'image' in request.files:
            image_file = request.files['image']
            image_name = image_file.filename
            direct_link = PostImagesUploader.upload_image_to_postimg(image_file, image_name)

        # Check if a URL is provided
        elif 'url' in request.form:
            image_url = request.form['url']
            response = requests.get(image_url)
            if response.status_code == 200:
                image_file = BytesIO(response.content)
                image_name = image_url.split("/")[-1]
                direct_link = PostImagesUploader.upload_image_to_postimg(image_file, image_name)
            else:
                return Response("Failed to fetch image from URL.", status=400)

        else:
            return Response("No image file or URL provided.", status=400)

        if direct_link:
            return Response(direct_link, status=200, mimetype='text/plain')
        else:
            return Response("Failed to upload the image.", status=500)

    except Exception as e:
        return Response(str(e), status=500)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Server is running"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
