# -*- coding: utf-8 -*-

import os

from db import db
from flask import request, url_for


class ModelImagesProduct(db.Model):
    __tablename__ = "images"
    id_image = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(80))
    id_product = db.Column(db.Integer, db.ForeignKey(
        "product.id_product"), nullable=False)

    def __init__(self, path, id_product):
        self.path = path
        self.id_product = id_product

    def list_images(self):
        return {
            "id": self.id_image,
            "url": request.url_root[:-1] + url_for("api.static", filename="images/{}".format(self.path))
        }

    @classmethod
    def find_image(cls, id_image):

        if not id_image:
            return None

        image = cls.query.filter_by(id_image=id_image).first()

        if image:
            return image
        return None

    def delete_image(self):

        path = "static/images/{}".format(self.path)
        os.remove(path)
        db.session.delete(self)
        db.session.commit()
