#!/usr/bin/env python

from webtest import TestApp
from webtest import Upload
from app import app

def test_index():
    app = TestApp(app)
    assert app.get('/').status_int == 200
    assert "Chargez le fichier à analyser" in  app.get('/').text 

# class TestUserInput:
#     def test_upload_file(self):
#         # """Test can upload file"""
#         # data['file'] = (io.BytesIO(b"abcdef"), 'test.jpg')
#         # self.login()
#         # response = self.client.post(
#         #     url_for('adverts.save'), data=data, follow_redirects=True,
#         #     content_type='multipart/form-data'
#         # )
#         # self.assertIn(b'Your item has been saved.', response.data)
#         # advert = Item.query.get(1)
#         # self.assertIsNotNone(item.logo)
#         pass