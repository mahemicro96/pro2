from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import MyFileSerializer
import io
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse
from rest_framework.parsers import JSONParser
from app2.models import MyFile
import cv2
import pybase64
from PIL import Image,ImageOps
import base64
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
import numpy as np
def pill(image_io):
	im = Image.open(image_io)
	ltrb_border = (0, 0, 0, 10)
	im_with_border = ImageOps.expand(im, border=ltrb_border, fill='white')
	buffer = BytesIO()
	im_with_border.save(fp=buffer, format='JPEG')
	buff_val = buffer.getvalue()
	return ContentFile(buff_val)
class MyFileView(APIView):

		def get(self, request, *args, **kwargs):
				p=request.data['id']
				emp = MyFile.objects.get(id=p)
				x=emp.file
				x=x.read()
				im4 = Image.open(io.BytesIO(x))
				numpy_image = np.array(im4)
				op = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
				gray = cv2.cvtColor(op, cv2.COLOR_BGR2GRAY)

				faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
				faces = faceCascade.detectMultiScale(gray,scaleFactor=1.3,minNeighbors=3,minSize=(30, 30))

				for (x, y, w, h) in faces:
					cv2.rectangle(op, (x, y), (x + w, y + h), (0, 255, 0), 2)
				bw = Image.fromarray(cv2.cvtColor(op, cv2.COLOR_BGR2RGB))
				#bw = im4.convert('L')
				imgByteArr = io.BytesIO()
				bw.save(imgByteArr, format='PNG')
				imgB = imgByteArr.getvalue()
				serializer = MyFileSerializer(emp)
				y=serializer.data
				str = pybase64.urlsafe_b64encode(imgB)
				y["im"] = str
				json_data =  JSONRenderer().render(y)
				im4.load()
				bw.load()
				return HttpResponse(json_data, content_type='application/json')

		parser_classes = (JSONParser,MultiPartParser, FormParser)

		def post(self,  request, *args, **kwargs):
				x=request.data['file']
				x=x.encode()
				x=pybase64.urlsafe_b64decode(x)
				fh = open("t602.jpg", "wb")
				fh.write(x)
				fh.close()
				pillow_image = pill("t602.jpg")
				image_file = InMemoryUploadedFile(pillow_image, None, 'foo.jpg', 'image/jpeg', pillow_image.tell, None)
				request.data['file'] = image_file
				file_serializer = MyFileSerializer(data=request.data)
				if file_serializer.is_valid():
						file_serializer.save()
						return Response(file_serializer.data, status=status.HTTP_201_CREATED)
				else:
						return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)