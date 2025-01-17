# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        persisted_id = product.id
        product.description = "Updated description"
        product.update()

        self.assertEqual(product.id, persisted_id)
        self.assertEqual(product.description, "Updated description")

        all_product_list = Product.all()
        self.assertEqual(len(all_product_list), 1)
        self.assertEqual(all_product_list[0].id, persisted_id)
        self.assertEqual(all_product_list[0].description, "Updated description")

    def test_update_a_product_with_no_id(self):
        """It should throw an Exception when trying to Update a Product with ID set to None"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        product.id = None
        product.description = "Updated description"
        with self.assertRaises(DataValidationError):
            product.update()

    def test_deserialize_a_product_with_invalid_availability(self):
        """It should throw an Exception when trying to deserialize a Product with Availability set not to a Bool value"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        serialized_product = product.serialize()
        serialized_product["available"] = "I'm not a Bool"

        with self.assertRaises(DataValidationError):
            product.deserialize(serialized_product)

    def test_deserialize_a_product_with_invalid_data(self):
        """It should throw an Exception when trying to deserialize a Product with invalid data"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        serialized_product = product.serialize()
        serialized_product["category"] = None

        with self.assertRaises(DataValidationError):
            product.deserialize(serialized_product)

    def test_deserialize_a_product_with_missing_data(self):
        """It should throw an Exception when trying to deserialize a Product with missing data"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        serialized_product = product.serialize()
        serialized_product["category"] = "Wrong data"

        with self.assertRaises(DataValidationError):
            product.deserialize(serialized_product)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        all_product_list = Product.all()
        self.assertEqual(len(all_product_list), 1)

        product.delete()
        all_product_list = Product.all()
        self.assertEqual(len(all_product_list), 0)

    def test_get_all_products(self):
        """It should load all Products from database"""
        all_product_list = Product.all()
        self.assertEqual(all_product_list, [])

        new_product_list = ProductFactory.create_batch(5)
        for product in new_product_list:
            product.create()

        all_product_list = Product.all()
        self.assertEqual(len(all_product_list), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        new_product_list = ProductFactory.create_batch(5)
        for product in new_product_list:
            product.create()

        name = new_product_list[0].name
        products_by_name_count = len([product for product in new_product_list if product.name == name])
        found = Product.find_by_name(name)

        self.assertEqual(found.count(), products_by_name_count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        new_product_list = ProductFactory.create_batch(10)
        for product in new_product_list:
            product.create()

        available = new_product_list[0].available
        available_product_count = len([product for product in new_product_list if product.available == available])
        found = Product.find_by_availability(available)

        self.assertEqual(found.count(), available_product_count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        new_product_list = ProductFactory.create_batch(10)
        for product in new_product_list:
            product.create()

        category = new_product_list[0].category
        products_by_category_count = len([product for product in new_product_list if product.category == category])
        found = Product.find_by_category(category)

        self.assertEqual(found.count(), products_by_category_count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        new_product_list = ProductFactory.create_batch(10)
        for product in new_product_list:
            product.create()

        price = new_product_list[0].price
        products_by_price_count = len([product for product in new_product_list if product.price == price])
        # Converting price to string to cover line 220 from models.py
        found = Product.find_by_price(str(price))

        self.assertEqual(found.count(), products_by_price_count)
        for product in found:
            self.assertEqual(product.price, price)
