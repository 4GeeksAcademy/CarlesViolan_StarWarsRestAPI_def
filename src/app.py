import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, People, favorite_planets

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuración de la base de datos
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Cambia esto por una clave secreta fuerte en producción
jwt = JWTManager(app)

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Manejo de errores
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generación del sitemap
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# Autenticación de usuarios para obtener el token JWT
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user = User.query.filter_by(email=email, password=password).first()
    if user is None:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# Endpoints para usuarios
@app.route('/user', methods=['GET'])
def handle_users():
    users_query = User.query.all()
    all_users = list(map(lambda x: x.serialize(), users_query))
    return jsonify(all_users), 200

# Endpoints para  User con ID
@app.route('/user/<int:user_id>', methods=['GET'])
def handle_specific_user(user_id):
    user_query = User.query.get(user_id)
    if user_query is None:
        raise APIException('User not found', status_code=404)
    specific_user = user_query.serialize()
    return jsonify(specific_user), 200

# Endpoints para current User
@app.route("/current-user", methods=["GET"])
@jwt_required()
def get_current_user():
    # Access the identity of the current user with get_jwt_identity
    current_user_id = get_jwt_identity()
    print("\n\n\n")
    print(current_user_id)

    if current_user_id is None:
        return jsonify({"msg": "User not found"}), 401
    
    user_query = User.query.get(current_user_id)
    print(user_query)

    if user_query is None:
        return jsonify({"msg": "User not found"}), 401

    user = user_query.serialize()
    print(user)
    print("\n\n\n")
    return jsonify(current_user=user), 200


# Endpoints para planetas
@app.route('/planet', methods=['GET'])
def handle_planets():
    planets_query = Planet.query.all()
    all_planets = list(map(lambda x: x.serialize(), planets_query))
    return jsonify(all_planets), 200

@app.route('/planet/<int:planet_id>', methods=['GET'])
def handle_specific_planet(planet_id):
    planet_query = Planet.query.get(planet_id)
    if planet_query is None:
        raise APIException('Planet not found', status_code=404)
    specific_planet = planet_query.serialize()
    return jsonify(specific_planet), 200

# Endpoints para personas
@app.route('/people', methods=['GET'])
def handle_people():
    people_query = People.query.all()
    all_people = list(map(lambda x: x.serialize(), people_query))
    return jsonify(all_people), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def handle_specific_people(people_id):
    people_query = People.query.get(people_id)
    if people_query is None:
        raise APIException('People not found', status_code=404)
    specific_people = people_query.serialize()
    return jsonify(specific_people), 200

@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_specific_people(people_id):
    people1 = People.query.get(people_id)
    if people1 is None:
        raise APIException('People not found', status_code=404)
    db.session.delete(people1)
    db.session.commit()
    return "Deleted", 200

# Endpoint para listar todos los favoritos del usuario actual
@app.route('/user/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    
    # Obtener los planetas favoritos
    favorite_planets = user.favorite_planets
    favorite_planets_list = list(map(lambda planet: planet.serialize(), favorite_planets))

    # Obtener las personas favoritas
    favorite_people = user.favorite_people
    favorite_people_list = list(map(lambda people: people.serialize(), favorite_people))

    # Retornar ambos en un solo JSON
    return jsonify({
        "favorite_planets": favorite_planets_list,
        "favorite_people": favorite_people_list
    }), 200


# Endpoint para añadir planetas favoritos
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
@jwt_required()
def add_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    planet = Planet.query.get(planet_id)
    if planet is None:
        raise APIException('Planet not found', status_code=404)

    user.favorite_planets.append(planet)
    db.session.commit()
    return jsonify({"msg": "Planet added to favorites"}), 200

# Endpoint para eliminar planetas favoritos
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    planet = Planet.query.get(planet_id)
    if planet is None:
        raise APIException('Planet not found', status_code=404)

    user.favorite_planets.remove(planet)
    db.session.commit()
    return jsonify({"msg": "Planet deleted to favorites"}), 200



# Nuevo endpoint para obtener los planetas favoritos del usuario actual
@app.route('/user/favorites/planets', methods=['GET'])
@jwt_required()
def get_user_favorite_planets():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    favorite_planets = user.favorite_planets
    favorite_planets_list = list(map(lambda planet: planet.serialize(), favorite_planets))
    return jsonify(favorite_planets_list), 200


# Endpoint para añadir people favoritos
@app.route('/favorite/people/<int:people_id>', methods=['POST'])
@jwt_required()
def add_favorite_people(people_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    people = People.query.get(people_id)
    if people is None:
        raise APIException('People not found', status_code=404)

    user.favorite_people.append(people)
    db.session.commit()
    return jsonify({"msg": "People added to favorites"}), 200

# Endpoint para eliminar people favoritos
@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_people(people_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    people = People.query.get(people_id)
    if people is None:
        raise APIException('People not found', status_code=404)

    user.favorite_people.remove(people)
    db.session.commit()
    return jsonify({"msg": "People remove to favorites"}), 200


# Nuevo endpoint para obtener las people favoritos del usuario actual
@app.route('/user/favorites/people', methods=['GET'])
@jwt_required()
def get_user_favorite_people():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        raise APIException('User not found', status_code=404)
    favorite_people = user.favorite_people
    favorite_people_list = list(map(lambda planet: planet.serialize(), favorite_people))
    return jsonify(favorite_people_list), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)