from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_fontawesome import FontAwesome
from flask_msearch import Search


app = Flask(__name__)
fa = FontAwesome(app)
app.config['SQLALCHEMY_DATABASE_URI']= 'mysql+pymysql://root:Uche_123@localhost/ecommerce'
app.config['SECRET_KEY'] = 'are you the owner'
bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'


search = Search(app)



from app import routes, models