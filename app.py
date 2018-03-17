from flask import Flask, request, redirect, url_for, g, render_template
from flask_mongoalchemy import MongoAlchemy
#from flask.ext.mongoalchemy import MongoAlchemy
from flaskext.auth import Auth, AuthUser, login_required, logout, get_current_user_data, encrypt
from stellar_base.address import Address
from decimal import *
import datetime
import requests
import blocktrail

app = Flask(__name__)

app.config['MONGOALCHEMY_DATABASE'] = 'cryptowalletsviewer'
app.config['MONGOALCHEMY_SERVER'] = 'mongo.bashtothefuture.com'
db = MongoAlchemy(app)

auth = Auth(app, login_url_name='ulogin')
auth.user_timeout=0

blockcypher_token = '7dc49cbdcb2245758426621ba54bc345'


class User(db.Document):
    #userId = db.IntField()
    username = db.StringField()
    password = db.StringField()

class Post(db.Document):
    created = db.DateTimeField()
    title = db.StringField()
    comment = db.StringField()

class Page(db.Document):
    created = db.DateTimeField()
    title = db.StringField()
    content = db.StringField()

class Comment(db.Document):
    created = db.DateTimeField()
    comment = db.StringField()
    name = db.StringField()
    email = db.StringField()
    post_id = db.StringField()

class Blog(db.Document):
    title = db.StringField()
    subtitle = db.StringField()

class Brand(db.Document):
    brand = db.StringField()

class Wallets(db.Document):
    coin = db.StringField()
    address = db.StringField()
    username = db.StringField()
    balance = db.FloatField()
    error = db.StringField()


@app.before_request
def init_users():
    user = None
    # first try to get admin user if null then procee to setup
    try:
        user = User.query.filter(User.username == 'admin').first()
        #user = User.query.filter(User.username==username).one()
    except:
        pass

    # TODO: find a way to not have this run all the time, SO SLOW!

    # if admin collection is empty need to create with default creds
    if user is None:
        #userId = 0
        username = "admin"
        password = "password"
        auth = AuthUser(username=username)
        auth.set_and_encrypt_password(password, salt='1234567')
        myuser = User(username=username, password=auth.password)
        myuser.save()

        brand = Brand.query.first()
        #return render_template('setup.html', brand=brand)
        return redirect(url_for('ulogin'))
    ##elif user is not None:
        ##authAdmin = AuthUser(username=user.username)
        ##authAdmin.set_and_encrypt_password(user.password, salt='1234567')

        # TODO: scale users list, currently just single user mode
        #g.users = {'admin': authAdmin}
        #g.users = User.query

@login_required()
def index():
    if request.method == 'POST':
        title = request.form['title']
        comment = request.form['comment']
        post = Post(created=datetime.datetime.now, title=title, comment=comment)
        post.save()

    # get posts for listing
    posts = Post.query.descending(Post.created)
    blog = Blog.query.first()
    brand = Brand.query.first()
    pages = Page.query

    # NEED TO UPDATE FOR MULTIPLE ADDRESSES
    wallets = Wallets.query.filter(Wallets.username == get_current_user_data()["username"])

    # trying to get user login boolean
    user = get_current_user_data()

    return render_template('index.html', posts=posts, user=user, blog=blog, brand=brand, pages=pages, wallets=wallets)

def usignup():
    brand = Brand.query.first()
    pages = Page.query

    # IMPLEMENT SIGNUP CODE
    if request.method == 'POST':
        if request.form['password'] == request.form['confirmpassword']:
            #userId = 0
            username = request.form['username']
            password = request.form['password']
            auth = AuthUser(username=username)
            auth.set_and_encrypt_password(password, salt='1234567')
            myuser = User(username=username, password=auth.password)
            myuser.save()

    return render_template('signup.html', user=get_current_user_data(), brand=brand, pages=pages)


def ulogin():
    # required for all areas to show brand and pages in menu
    brand = Brand.query.first()
    pages = Page.query
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter(User.username==username).first()

        if user is not None:
            authUser = AuthUser(username=username, salt='1234567')
            authUser.password = user.password
            #if authUser.authenticate(encrypt(password, salt='1234567')):
            if authUser.authenticate(request.form['password']):
                return redirect(url_for('index'))

        return 'Failure :('

    return render_template('login.html', user=get_current_user_data(), brand=brand, pages=pages)


@login_required()
def profile():
    # required for all areas to show brand and pages in menu
    brand = Brand.query.first()
    pages = Page.query
    #if get_current_user_data()["username"] != "admin":
    #    return redirect(url_for('index'))

    if request.method == 'POST':
        if request.form['password'] == request.form['confirmpassword']:
            #userId = 0
            username = get_current_user_data()["username"]
            password = request.form['password']
            # query mongo for user
            myUser = User.query.filter(User.username==username).first()
            myAuth = AuthUser(username=username)
            myAuth.set_and_encrypt_password(password, salt='1234567')
            myUser.password = myAuth.password
            myUser.save()

    return render_template('profile.html', brand=brand, pages=pages, user=get_current_user_data())



@login_required()
def admin():
    if get_current_user_data()["username"] != "admin":
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        comment = request.form['comment']
        time = datetime.datetime.today()
        post = Post(created=time, title=title, comment=comment)
        post.save()

    # get posts for listing
    posts = Post.query.descending(Post.created)
    brand = Brand.query.first()
    blog = Blog.query.first()
    pages = Page.query
    return render_template('admin.html', posts=posts, user=get_current_user_data(), brand=brand, blog=blog, pages=pages)

#@login_required()
def ulogout():
    logout()
    return redirect(url_for('index'))

@app.route('/title', methods=['POST'])
@login_required()
def title():
    title = request.form['blogTitle']
    subtitle = request.form['blogSubTitle']
    # get title info from mongodb
    blog = Blog.query.first()
    if blog == None:
        blog = Blog(title=title, subtitle=subtitle)
    else:
        blog.title = title
        blog.subtitle = subtitle
    blog.save()
    return redirect(url_for('admin'))


@login_required()
@app.route('/addaddress', methods=['POST'])
def addaddress():
    myAddress = request.form['address']
    myCoin = request.form['coin']
    address = Wallets(coin=myCoin, address=myAddress, username=get_current_user_data()["username"], balance=10101010, error='')
    address.save()
    return redirect(url_for('index'))


@login_required()
@app.route('/setbrand', methods=['POST'])
def setbrand():
    mybrand = request.form['brand']
    brand = Brand.query.first()
    if brand == None:
        brand = Brand(brand=mybrand)
    else:
        brand.brand = mybrand
    brand.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/postremove/<id>', methods=['GET'])
def deletepost(id):
    mypost = Post.query.get(id)
    mypost.remove()
    return redirect(url_for('admin'))

@login_required()
@app.route('/postedit/<id>', methods=['GET', 'POST'])
def editpost(id):
    mypost = Post.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    # if POST then save new post data
    if request.method == 'POST':
        title = request.form['title']
        comment = request.form['comment']
        time = datetime.datetime.today()
        mypost.title = title
        mypost.comment = comment
        mypost.created = time
        mypost.save()
        return redirect(url_for('admin'))

    return render_template('postedit.html', post=mypost, user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
@app.route('/pageadd', methods=['POST'])
def addpage():
    title = request.form['title']
    content = request.form['content']
    time = datetime.datetime.today()
    page = Page(created=time, title=title, content=content)
    page.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/pageremove/<id>', methods=['GET'])
def deletepage(id):
    mypage = Page.query.get(id)
    mypage.remove()
    return redirect(url_for('admin'))

@login_required()
@app.route('/pageedit/<id>', methods=['GET', 'POST'])
def editpage(id):
    mypage = Page.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    # if POST then save new post data
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        time = datetime.datetime.today()
        mypage.title = title
        mypage.content = content
        mypage.created = time
        mypage.save()
        return redirect(url_for('admin'))

    return render_template('pageedit.html', page=mypage, user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
@app.route('/pages/<id>', methods=['GET'])
def viewpage(id):
    mypage = Page.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    return render_template('page.html', page=mypage, user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
@app.route('/posts/<id>', methods=['GET'])
def viewpost(id):
    mypost = Post.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    comments = Comment.query.filter(Comment.post_id == id)
    return render_template('post.html', post=mypost, user=get_current_user_data(), brand=brand, pages=pages, comments=comments, ccount=comments.count())

@app.route('/setup', methods=['POST'])
def setup():
    username = request.form['username']
    password = request.form['password']
    auth = AuthUser(username=username)
    auth.set_and_encrypt_password(password, salt='1234567')

    myuser = User(username="something")
    myuser.password = "somethingelse"
    myuser.save()

    brand = Brand.query.first()
    pages = Page.query
    #return render_template('login.html', user=get_current_user_data(), brand=brand, pages=pages)
    return redirect(url_for('ulogin'))

@login_required()
@app.route('/changepass', methods=['POST'])
def changepass():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter(User.username == username).first()
    user.password = password
    user.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/comment/<id>', methods=['GET', 'POST'])
def comment(id):
    brand = Brand.query.first()
    pages = Page.query
    if request.method == 'POST':
        comment = request.form['comment']
        name = request.form['name']
        email = request.form['email']
        time = datetime.datetime.today()
        mycomment = Comment(created=time, comment=comment, name=name, email=email, post_id=id)
        mycomment.save()
        return redirect(url_for('viewpost', id=id))

def get_comment_count(id):
    comments = Comment.query.filter(Comment.post_id == str(id))
    return comments.count()

def getBalance(wallet):
    # Dummy default balance
    bal = [{"value": 10101010}]

    #if hasattr(wallet, 'balance'):
    #    return wallet.balance
    if wallet.balance != 10101010:
        return wallet.balance
    elif wallet.balance == 99999999:
        return wallet.error
    else:
        refreshSingleWallet(wallet)

def refreshSingleWallet(wallet):
    print wallet.address

    # Bitcoin Cash balance lookup
    #if wallet.coin == "bch":
        #client = blocktrail.APIClient(api_key="27624245730869da2e0ea49573486a50658d3d2f", api_secret="eb55ec22439129cb8ed85d0570324edca80a061a", network="BCH", testnet=False)
        #address = client.address(wallet.address)
        #latest_block = client.block_latest()

        ## need to check this for errors
        #wallet.balance = address['balance']
        #wallet.error = ''
        #wallet.save()
        #return wallet.balance


    # Ripple balance lookup
    if wallet.coin == "xrp":
        balanceReturn = requests.get('https://data.ripple.com/v2/accounts/' + wallet.address + '/balances')
        if (balanceReturn.status_code == 400) or (balanceReturn.status_code == 404):
            wallet.error = balanceReturn.json()["message"]
            wallet.balance = 99999999
            wallet.save()
            return balanceReturn.json()["message"]
        elif balanceReturn.status_code == 200:
            #return balanceReturn.json()["balances"][0]["value"]
            wallet.balance = float(balanceReturn.json()["balances"][0]["value"])
            wallet.error = ''
            wallet.save()
            return wallet.balance

    # Bitcoin balance lookup
    if wallet.coin == "btc":
        balanceReturn = requests.get('https://api.blockcypher.com/v1/btc/main/addrs/' + wallet.address + '/balance?token=' + blockcypher_token)
        if (balanceReturn.status_code == 400) or (balanceReturn.status_code == 404)or (balanceReturn.status_code == 429):
            wallet.error = balanceReturn.json()["error"]
            wallet.balance = 99999999
            wallet.save()
            return balanceReturn.json()["error"]
        else:
            # convert satoshi to BTC
            wallet.balance = float(Decimal(balanceReturn.json()["balance"]) / Decimal(100000000))
            wallet.error = ''
            wallet.save()
            return wallet.balance

    # Litecoin balance lookup
    if wallet.coin == "ltc":
        balanceReturn = requests.get('https://api.blockcypher.com/v1/ltc/main/addrs/' + wallet.address + '/balance?token=' + blockcypher_token)
        if (balanceReturn.status_code == 400) or (balanceReturn.status_code == 404)or (balanceReturn.status_code == 429):
            wallet.error = balanceReturn.json()["error"]
            wallet.balance = 99999999
            wallet.save()
            return balanceReturn.json()["error"]
        else:
            wallet.balance = float(Decimal(balanceReturn.json()["balance"]) / Decimal(100000000))
            wallet.error = ''
            wallet.save()
            return wallet.balance

    # Ethereum balance lookup
    if wallet.coin == "eth":
        balanceReturn = requests.get('https://api.blockcypher.com/v1/eth/main/addrs/' + wallet.address + '/balance?token=' + blockcypher_token)
        if (balanceReturn.status_code == 400) or (balanceReturn.status_code == 404)or (balanceReturn.status_code == 429):
            wallet.error = balanceReturn.json()["error"]
            wallet.balance = 99999999
            wallet.save()
            return balanceReturn.json()["error"]
        else:
            wallet.balance = float(Decimal(balanceReturn.json()["balance"]) / Decimal(1000000000000000000))
            wallet.error = ''
            wallet.save()
            return wallet.balance

    # Stellar balance lookup
    if wallet.coin == "xlm":
        address = Address(address=wallet.address, network='public')
        try:
            address.get()
        except:
            wallet.error = "Error"
            wallet.balance = 99999999
            wallet.save()
            return "Error"

        wallet.balance = float(address.balances[0]["balance"])
        wallet.error = ''
        wallet.save()
        return wallet.balance

    # Verge balance lookup
    if wallet.coin == "xvg":
        balanceReturn = requests.get('https://verge-blockchain.info/ext/getbalance/' + wallet.address)
        if isinstance(balanceReturn.json(), float):
            wallet.balance = float(balanceReturn.json())
            wallet.error = ''
            wallet.save()
            return wallet.balance
        else:
            wallet.error = balanceReturn.json()["error"]
            wallet.balance = 99999999
            wallet.save()
            return balanceReturn.json()["error"]

    # If none of these, return dummy value (for dev)
    #return bal

def refreshAllWallets():
    wallets = Wallets.query.filter(Wallets.username == get_current_user_data()["username"])
    for myWallet in wallets:
        refreshSingleWallet(myWallet)
    #return redirect(url_for('index'))

@login_required()
@app.route('/walletremove/<id>', methods=['GET'])
def deletewallet(id):
    mywallet = Wallets.query.get(id)
    mywallet.remove()
    return redirect(url_for('index'))

@login_required()
@app.route('/walletrefresh/<id>', methods=['GET'])
def refreshwallet(id):
    mywallet = Wallets.query.get(id)
    refreshSingleWallet(mywallet)
    return redirect(url_for('index'))

@login_required()
@app.route('/walletrefreshall', methods=['GET'])
def refreshwalletall():
    refreshAllWallets()
    return redirect(url_for('index'))


app.add_url_rule('/', 'index', index, methods=['GET', 'POST'])
app.add_url_rule('/admin/', 'admin', admin, methods=['GET', 'POST'])
app.add_url_rule('/profile/', 'profile', profile, methods=['GET', 'POST'])
app.add_url_rule('/logout/', 'ulogout', ulogout)
app.add_url_rule('/login/', 'ulogin', ulogin, methods=['GET', 'POST'])
app.add_url_rule('/signup/', 'usignup', usignup, methods=['GET', 'POST'])

app.secret_key = 'N4BUdSXUzHxNoO8g'

if __name__ == '__main__':
    app.jinja_env.globals.update(get_comment_count=get_comment_count)
    app.jinja_env.globals.update(getBalance=getBalance)
    app.run(debug=True,host='0.0.0.0')
