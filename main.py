from flask import Flask, url_for
from flask import render_template
from flask import request
from flask import jsonify
from flask import session
from flask import redirect
import requests as req
import re
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token
import datetime
import uuid
import pymongo
import ssl
import ast
import secrets

# dev import to run locally
import os

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'ad-lab-wb-21-10-04-51bba8aad6df.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = filename

firebase_request_adapter = requests.Request()
datastore_client = datastore.Client()

app = Flask(__name__)
app.secret_key = secrets.secret_key

# moved function to top as it was referenced in one of the mongo functions


def getDatastore(key, id):
    productQuery = datastore_client.query()
    firstProductKey = datastore_client.key(
        f"{key}", f"{id}")
    productQuery.key_filter(firstProductKey, "=")
    productResults = list(productQuery.fetch())
    # print(type(productResults))
    # print(productResults)
    return productResults

# Mongo setup


conn_str = secrets.conn_str
client = pymongo.MongoClient(
    conn_str, serverSelectionTimeoutMS=5000, tls=True, tlsAllowInvalidCertificates=True)
db = client.test
try:
    client.server_info()
except Exception:
    print("Unable to connect to mongoDB server.")

# mongo CREATE user


def mongoCreateUser(name="none", email="none"):
    db.users.insert_one(
        {
            "name": name,
            "email": email,
            "purchaseHistory": [],
            "orders": []
        }
    )

    return str(mongoReadOne(email))


# mongo READ one
def mongoReadOne(email):
    cursor = db.users.find({"email": email}).limit(1)
    try:
        return cursor[0]
    except:
        return False


# mongo READ many
def mongoReadMany():
    cursor = db.users.find({})
    # for document in cursor:
    #     print(document)
    return cursor


# mongo UPDATE add order
def mongoAddOrder(email, productId, orderStatus="in-warehouse"):

    # check if order already exists for product + user combo
    try:
        thisOrder = db.users.find(
            {"email": email,
                "orders": {"$elemMatch": {"productId": productId}}}
        )
        # this will create an exception if order isn't already present
        thisOrder[0]
        print("order already exists, updating")

        thisOrder = db.users.update_one(
            {"email": email, "orders.productId": productId},
            {"$set": {"orders.$.status": orderStatus}}
        )

        print("order updated")
    except Exception as e:
        print("adding order to db")

        # order not in db, add
        query = {"email": email}
        newValues = {"$push": {"orders": {
            "productId": productId, "status": orderStatus}}}

        db.users.update_one(query, newValues)

    return mongoReadOne(email)

# mongo UPDATE add to purchase history


def mongoAddPurchase(email, productId):
    query = {"email": email}
    newValues = {"$push": {"purchaseHistory": productId}}

    db.users.update_one(query, newValues)
    return mongoReadOne(email)


# mongo UPDATE customer information
def mongoUpdateCustomer(email, name, address):
    query = {"email": email}
    newValues = {"$set": {"name": name, "address": address}}
    db.users.update_one(query, newValues)
    return mongoReadOne(email)


# mongo DELETE order
def mongoDeleteOrder(email, productId):
    query = {"email": email}
    instruction = {"$pull": {"orders": {"productId": productId}}}

    db.users.update_one(query, instruction)

    return mongoReadOne(email)


# mongo DELETE customer

def mongoDeleteCustomer(email):
    query = {"email": email}
    db.users.delete_one(query)

    allCurrentUsers = mongoReadMany()

    allUsersStr = ""
    for user in allCurrentUsers:
        allUsersStr += str(user) + "<br><hr><br>"

    return allUsersStr


def mongoListOrders():
    orders = []
    allUsers = mongoReadMany()
    for user in allUsers:
        if user['orders'] != []:
            for order in user['orders']:
                order['email'] = user['email']
                thisProductData = getDatastore(
                    "product", order['productId'])[0]
                order['productName'] = thisProductData['productName']
                order['price'] = thisProductData['price']

            # print(user['orders'])
            orders += user['orders']
    # print(orders)
    return orders


@app.route("/signIn")
def signIn():
    # Verify Firebase auth.
    id_token = request.cookies.get("token")
    error_message = None
    global claims
    claims = None

    if id_token != "":
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            session['user'] = claims
            print(claims)
        except ValueError as exc:
            error_message = str(exc)
            return error_message
    else:
        print("id token=''")

    if not session.get('user'):
        print("user session not found")
        return "error, session not found"
    # check if user exists
    if mongoReadOne(session['user']['email']):
        print("user in database")
        return redirect(url_for('index'))
    else:
        print("user not found on database")
        try:
            # google based user with name in claims var
            name = session['user']['name']
        except Exception as e:
            # admin user with no name param in claims
            name = "admin"
        email = session['user']['email']
        mongoCreateUser(name=name, email=email)
        return redirect(url_for('index'))


@app.route("/test/mongo/createUser")
def mongoCreateUserRoute():
    return str(mongoCreateUser("newUserName", "mongoTestEmail"))


@app.route("/test/mongo/readOne")
def mongoReadOneRoute():
    return str(mongoReadOne("mongoTestEmail"))


@app.route("/test/mongo/readMany")
def mongoReadManyRoute():

    allCurrentUsers = mongoReadMany()

    allUsersStr = ""
    for user in allCurrentUsers:
        allUsersStr += str(user) + "<br><hr><br>"

    return allUsersStr


@app.route("/test/mongo/addOrder")
def mongoAddOrderRoute():
    return str(mongoAddOrder("mongoTestEmail", "testProductID"))


@app.route("/test/mongo/addPurchase")
def mongoAddPurchaseRoute():
    return str(mongoAddPurchase("mongoTestEmail", "newPurchaseID"))


@app.route("/test/mongo/updateCustomer")
def mongoUpdateCustomerRoute():
    return str(mongoUpdateCustomer("mongoTestEmail", "newName", "newAddress"))


@app.route("/test/mongo/deleteOrder")
def mongoDeleteOrderRoute():
    return str(mongoDeleteOrder("REDACTED", "161d6bb8-e0a0-44fd-b28c-5219ea4e3322"))


@app.route("/test/mongo/deleteUser")
def mongoDeleteCustomerRoute():
    return str(mongoDeleteCustomer("mongoTestEmail"))


@app.route("/", methods=["GET"])
def index():
    products = listProducts()

    return render_template('index.html', topPicks=products[0:3], saleItems=products[3:])


@app.route("/about", methods=["POST", "GET"])
def about():
    return render_template("about.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    return render_template("login.html")


@app.route("/purchase/<productID>", methods=["POST", "GET"])
def makePurchase(productID):
    try:
        email = session['user']['email']
        mongoAddOrder(email, productID)
    except Exception as e:
        print("order could not be made")
    return "<p>make purchase called</p>"


@app.route("/orders/")
def orders():
    # disallow logged out / admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "google.com":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    email = session['user']['email']
    user = db.users.find({"email": email})[0]

    # check if user has any orders
    hasOrders = False
    userOrders = user['orders']
    orderList = []
    idList = []

    if userOrders != []:
        print("user has orders")
        hasOrders = True
        for order in userOrders:
            orderList += getDatastore("product", order['productId'])
        # print(orderList[0].key.Key)
        # create separate list of result id's

        for order in orderList:
            idList += re.findall(
                "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", str(order.key))

        print(idList)

        # bring id and product info together
        # list(zip(idList, results))
        print("orderList printout:")
        print(orderList)
        # bind product info relating to the order (datastore), and the order status (mongo) together
        orderInfo = list(zip(orderList, userOrders))
    else:
        print("user does not have orders")

    return render_template("orders.html", orders=orderList, hasOrders=hasOrders, userOrders=userOrders, orderInfo=orderInfo)


@app.route("/signout")
def signOut():
    session.pop("user", None)
    print("session destroyed")
    signOutResponse = jsonify(success=True)
    signOutResponse.status_code = 200
    return signOutResponse

# admin routes


@app.route("/admin/login", methods=["POST", "GET"])
def adminLogin():
    return render_template("admin_login.html")

# Datastore admin options page


@app.route("/admin")
def admin():
    # disallow non-admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "password":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    return render_template("admin_options.html")


@app.route("/admin/orderList")
def adminOrderList():
    # disallow non-admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "password":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    orders = mongoListOrders()

    return render_template("admin_order_list.html", orders=orders)


@app.route("/admin/deleteOrder/<productId>/<email>")
def adminDeleteOrder(productId, email):
    mongoDeleteOrder(email, productId)
    return redirect(url_for('adminOrderList'))


@app.route("/admin/updateOrder/<productId>/<email>", methods=["POST"])
def adminUpdateOrder(productId, email):
    status = request.form.get('status')
    # mongo add order allows updating existing as well
    mongoAddOrder(email, productId, orderStatus=status)
    return redirect(url_for('adminOrderList'))


@ app.route("/admin/orderDetails/<productId>/<email>")
def adminOrderDetails(productId, email):
    allOrders = mongoListOrders()
    print(allOrders)
    for order in allOrders:
        if order['productId'] == productId and order['email'] == email:
            thisOrder = order

    return render_template("update_order.html", order=thisOrder)


# DATASTORE CRUD

# create


@ app.route("/admin/addProduct", methods=["POST", "GET"])
def adminAddProduct():

    # disallow non-admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "password":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    if request.method == 'POST':
        with datastore_client.transaction():

            # bring in form data
            url = request.form.get('url')
            price = request.form.get('price')
            name = request.form.get('name')
            quantity = request.form.get('quantity')

            key = datastore_client.key("product", str(uuid.uuid4()))

            product = datastore_client.get(key)

            if not product:
                product = datastore.Entity(key)
                product.update(
                    {"imageUrl": f"{url}",
                     "price": f"{price}",
                     "productName": f"{name}",
                     "quantity": int(quantity)})
                datastore_client.put(product)

            print(product)
            # return product
            # return "see python console"
            return redirect(url_for('listProductsRoute'))

    else:
        return render_template("add_product.html")


# read

def listProducts():
    query = datastore_client.query(kind="product")
    query.add_filter("quantity", ">=", 1)
    query.order = ["-quantity"]
    results = list(query.fetch())
    # print(results)

    # create separate list of result id's
    strResults = str(results)
    idList = re.findall(
        "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", strResults)

    # bring id and product info together
    return list(zip(idList, results))


@ app.route("/admin/list-products")
def listProductsRoute():

    # disallow non-admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "password":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    products = listProducts()

    return render_template("admin_product_list.html", products=products)


@ app.route("/product/<id>")
def product(id):
    # get product information based on productId
    productQuery = datastore_client.query()
    firstProductKey = datastore_client.key(
        "product", f"{id}")
    productQuery.key_filter(firstProductKey, "=")
    productResults = list(productQuery.fetch())

    # get review information based on productId
    reviewQuery = datastore_client.query(kind='review')
    reviewQuery.add_filter('productID', '=', id)
    reviewResults = list(reviewQuery.fetch())

    # catch product not found errors
    try:
        formattedProductResults = re.findall("{.*}", str(productResults[0]))[0]

        productInfo = ast.literal_eval(formattedProductResults)

        # print(productInfo)

    except Exception as err:
        return str(err)

    # continue if no reviews are found for product
    try:
        formattedReviewResults = "["
        for review in reviewResults:
            formattedReviewResults += re.findall("{.*}", str(review))[0] + ","

        # remove trailing comma
        formattedReviewResults = formattedReviewResults[:-1]
        formattedReviewResults += "]"

        # convert str to array
        reviewInfo = ast.literal_eval(formattedReviewResults)

        totalRating = 0
        numReviews = 0
        for currReview in reviewInfo:
            totalRating += int(currReview['Rating'])
            numReviews += 1

        averageRating = round(totalRating / numReviews, 2)

    except Exception as err:
        print(f"no reviews found for product of id {id}")
        reviewInfo = False
        averageRating = False

    return render_template("product_details.html", productInfo=productInfo, reviewInfo=reviewInfo, averageRating=averageRating)


# update

@ app.route("/admin/updateProduct/<id>", methods=["POST", "GET"])
def adminUpdateProduct(id):

    # disallow non-admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "password":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    # this will require admin to see all products and select to get the ID in url

    if request.method == 'POST':
        with datastore_client.transaction():

            # bring in form data
            url = request.form.get('url')
            price = request.form.get('price')
            name = request.form.get('name')
            quantity = request.form.get('quantity')

            # get product in db
            key = datastore_client.key("product", f"{id}")
            product = datastore_client.get(key)

            # update product data
            product['imageUrl'] = url
            product['price'] = price
            product['productName'] = name
            product['quantity'] = quantity

            # push changes to gcloud
            datastore_client.put(product)

            if not product:
                product = datastore.Entity(key)
                product.update(
                    {"imageUrl": f"{url}",
                     "price": f"{price}",
                     "productName": f"{name}",
                     "quantity": int(quantity)})
                datastore_client.put(product)

            print(product)
            # return product
            # return "see python console"
            return redirect(url_for('listProductsRoute'))
    else:
        with datastore_client.transaction():

            # get product in db
            key = datastore_client.key("product", f"{id}")
            product = datastore_client.get(key)

            return render_template("update_product.html", product=product, id=id)

# delete


@ app.route("/admin/deleteProduct/<id>", methods=["GET", "POST"])
def deleteProduct(id):

    # disallow non-admin users access
    if session.get('user'):
        if session['user']['firebase']['sign_in_provider'] != "password":
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

    key = datastore_client.key("product", f"{id}")
    datastore_client.delete(key)
    return redirect(url_for('listProductsRoute'))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
