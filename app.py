import time
from datetime import datetime
from flask import Flask, render_template, redirect, request, session, flash
from model.user_model import User
from model.profile_model import Profile
from model.project_model import Project
from model.feature_model import Feature
from model.category_model import Category
from model.value_objects import UserProfile
from model.value_objects import ProjectStatus
from model.value_objects import FeatureStatus
from repository._database import Database
from services.user_service import UserService
from services.project_service import ProjectService


def trace(msg):
    print("DASHBOARD|{}| {}".format(time.strftime("%Y-%m-%d %H:%M"), msg))


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app = Flask(__name__, template_folder='./template', static_folder="./template/static")
app.secret_key = "dashboard-secret-key-2023"
trace("Application is running!")

database = Database()
database.connect()
trace("Database is connected!")

user_service = UserService(database)
project_service = ProjectService(database)

@app.errorhandler(404) 
def invalid_route(e): 
    return "Invalid route."

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect("/home")
    return render_template('index.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_email = request.form.get("email")
        user_passd = request.form.get("password")
        user = user_service.authenticate(user_email, user_passd)
        if user is not None:
            session["user_id"] = user.id
            session["user_name"] = user.first_name
            session["user_email"] = user.email
            session["user_profile"] = user.profile.name
            session["profile_id"] = user.profile.id
            session["profile_name"] = user.profile.name
            session["user_is_guest"] = user.profile.id == UserProfile.GUEST.id
            session["user_is_po"] = user.profile.id == UserProfile.PRODUCT_OWNER.id
            trace("Session started! User: {} ({})".format(user.first_name, user.profile.name))
            return redirect("/home" if user.profile.id != 1 else "/admin")
        else:
            trace("Access Denied for User {}.".format(user_email))
            flash("Acesso negado! Usuário ou senha inválidos. Digite novamente.")
    return render_template("index.html")


@app.route("/logout")
def logout():
    trace("Session finished! User: {} ({})".format(session['user_name'], session['user_profile']))
    session["user_id"] = None
    return redirect("/")


def list_all_granted_projects_for_user_in_current_session():
    if not session.get("user_id"):
        return []
    user_id = session.get("user_id")
    user = user_service.find_user_by_id(user_id)
    return project_service.get_all_granted_projects_of_user(user)


@app.route("/home")
def home():
    if not session.get("user_id"):
        return redirect("/login")

    granted_projects = list_all_granted_projects_for_user_in_current_session()
    return render_template("home.html", granted_projects=granted_projects)


@app.route("/admin")
def admin():
    if not session.get("user_id"):
        return redirect("/login")
    if session.get("user_profile").lower() != "admin":
        return redirect("/login")

    users = user_service.admin_get_all_users()
    profiles = UserProfile.List

    return render_template("admin.html", users=users, profiles=profiles)


@app.route("/usuario/trocar-perfil", methods=["POST"])
def change_profile():
    user_id = request.form['user_id']
    new_profile_id = request.form['new_profile']
    trace("Changing Profile of User {} to {}".format(user_id, new_profile_id))

    profile = Profile(new_profile_id, '')
    user = user_service.find_user_by_id(user_id)
    user = user_service.change_user_profile(user, profile)

    return redirect("/admin")


@app.route("/usuario/incluir", methods=["POST"])
def new_user():
    new_user_first_name = request.form['textNewUserFirstName']
    new_user_last_name = request.form['textNewUserLastName']
    new_user_email = request.form['textNewUserEmail']
    new_user_pass = request.form['textNewUserPassword']
    trace("Adding new User (FirstName: {}, LastName: {}, E-mail: {}".format(
        new_user_first_name, new_user_last_name, new_user_email))

    guest_profile = UserProfile.GUEST
    new_user = User(id=0, first_name=new_user_first_name, last_name=new_user_last_name,
                    email=new_user_email, password=new_user_pass, profile=guest_profile)
    new_user = user_service.add_new_user(new_user)

    if new_user is None:
        flash("Falha ao cadastrar novo usuário. Contacte o Administrador.")
        return redirect("/")

    trace(" --- New Password: '{}' ".format(new_user.password))
    flash(".Novo Usuário cadastrado. Verifique seu e-mail.")

    return redirect("/")


@app.route("/usuario/zerar-senha", methods=["POST"])
def forgot_password():
    user_email = request.form['textUserEmail']

    trace("Reseting User Password (E-mail: {}".format(user_email))

    user = user_service.find_user_by_email(user_email)
    if user is None:
        flash("Usuário não localizado.")
        return redirect("/")

    new_password = user_service.reset_password(user)

    flash(".Senha zerada com sucesso! Verifique seu e-mail.")

    return redirect("/")


@app.route("/usuario/trocar-senha", methods=["POST"])
def change_password():
    user_email = request.form['textUserEmail']
    user_old_pass = request.form['textUserOldPassword']
    user_new_pass = request.form['textUserNewPassword']
    user_confirm_pass = request.form['textUserConfirmPassword']

    if user_new_pass != user_confirm_pass:
        flash("As senhas não coincidem.")
        return redirect("/home")

    trace("Changing  User Password (E-mail: {}".format(user_email))

    user = user_service.find_user_by_email(user_email)
    if user is None:
        flash("Usuário não localizado.")
        return redirect("/home")

    user = user_service.authenticate(user_email, user_old_pass)
    if user is None:
        flash("Acesso negado! Usuário ou senha inválidos.")
        return redirect("/home")

    changed_pass = user_service.change_user_password(user, user_new_pass)
    if not changed_pass:
        flash("Falha ao trocar a senha. Contacte o Administrador.")
        return redirect("/home")

    flash(".Senha alterado com sucesso!")

    return redirect("/home")


@app.route("/usuario/remover", methods=["POST"])
def remove_user():
    user_id_to_remove = request.form['user_id_to_remove']
    trace("Removing User: {}".format(user_id_to_remove))

    user = user_service.find_user_by_id(user_id_to_remove)
    if user is None:
        flash("Falha ao remover o usuário (ID não localizado). Contacte o Administrador.")
        return redirect("/admin")

    user_was_removed = user_service.remove_user(user)
    if not user_was_removed:
        flash("Falha ao remover o usuário (Deleção falhou). Contacte o Administrador.")
        return redirect("/home")

    return redirect("/admin")


def current_session_po_user():
    print( 'current_session_po_user', 'aqui agora')
    try:
        user_id = session["user_id"]
        user = user_service.find_user_by_id(user_id)
    except:
        user = None

    if user is None:
        flash("Sessão Inválida.")
        return None
    if user.profile.id != UserProfile.PRODUCT_OWNER.id and user.profile.id != UserProfile.ADMIN.id:
        flash("Sem permissão para esta opção.")
        return None
    return user


@app.route("/projetos", methods=["GET"])
def list_projects():
    user = current_session_po_user()
    if user is None:
        return redirect("/")
    projects = project_service.get_all_owned_projects_of_user(user)
    if projects is None:
        flash("Falha ao carregar os projetos.")
        return redirect("/projetos")
    granted_projects = list_all_granted_projects_for_user_in_current_session()
    project = Project()
    return render_template("projects.html", granted_projects=granted_projects, projects=projects,
                           project_status=ProjectStatus, project=project)


@app.route("/projeto/incluir", methods=["POST"])
def new_project():
    user = current_session_po_user()
    if user is None:
        return redirect("/")
    projects = project_service.get_all_owned_projects_of_user(user)
    if projects is None:
        flash("Falha ao carregar os projetos. Contacte o Administrador.")
        return redirect("/")

    project_shortname = request.form["textProjectShortName"]
    project_name = request.form["textProjectName"]
    project_description = request.form["textProjectDescription"]
    project_status = request.form["selectProjectStatus"]

    project = Project(id=0, short_name=project_shortname, name=project_name,
                      description=project_description, status=project_status,
                      owner=user)
    try:
        project = project_service.add_new_project(project)
        if project is not None:
            return redirect("/projetos")
        flash("Falha ao gravar o projeto.")
    except Exception as err:
        err_string = str(err)
        if "exist" in err_string:
            flash("Projeto já existente com este codinome informado.")

    granted_projects = list_all_granted_projects_for_user_in_current_session()

    return render_template("projects.html", granted_projects=granted_projects, projects=projects,
                           project_status=ProjectStatus, project=project)


@app.route("/projeto/alterar", methods=["POST"])
def edit_project():
    user = current_session_po_user()
    if user is None:
        return redirect("/")
    projects = project_service.get_all_owned_projects_of_user(user)
    if projects is None:
        flash("Falha ao carregar os projetos. Contacte o Administrador.")
        return redirect("/")

    project_id = request.form["textProjectId"]
    project_shortname = request.form["textProjectShortName"]
    project_name = request.form["textProjectName"]
    project_description = request.form["textProjectDescription"]
    project_status = request.form["selectProjectStatus"]

    project = Project(id=project_id, short_name=project_shortname, name=project_name,
                      description=project_description, status=project_status,
                      owner=user)
    try:
        project = project_service.change_project_data(project)
        if project is not None:
            return redirect("/projeto/{}".format(project_id))
        flash("Falha ao alterar o projeto.")
    except Exception as err:
        err_string = str(err)
        if "exist" in err_string:
            flash("Projeto já existente com este codinome informado.")

    granted_projects = list_all_granted_projects_for_user_in_current_session()

    return render_template("project.html", granted_projects=granted_projects, project=project,
                           project_status=ProjectStatus)


@app.route("/projeto/remover", methods=["POST"])
def remove_project():
    user = current_session_po_user()
    if user is None:
        return redirect("/")

    project_id_to_remove = request.form['project_id_to_remove']
    trace("Removing Project: {}".format(project_id_to_remove))

    project = project_service.find_project_by_id(project_id_to_remove)
    if project is None:
        flash("Falha ao remover o projeto (ID não localizado). Contacte o Administrador.")
        return redirect("/home")

    project_was_removed = project_service.remove_project(project)
    if not project_was_removed:
        flash("Falha ao remover o projeto (Deleção falhou). Contacte o Administrador.")
        return redirect("/home")

    return redirect("/projetos")


@app.route("/projeto/<project_id>", methods=["GET", "POST"])
def change_project(project_id):
    user = current_session_po_user()
    if user is None:
        return redirect("/")

    project = project_service.find_project_by_id(project_id)
    if project is None:
        flash("Projeto não localizado (ID: {}).".format(project_id))
        return redirect("/home")

    project = project_service.load_project_by_id(project.id)
    granted_projects = list_all_granted_projects_for_user_in_current_session()

    return render_template("project.html", granted_projects=granted_projects, project=project,
                           project_status=ProjectStatus, feature_status=FeatureStatus)


@app.route("/projeto/<project_id>/categoria", methods=["POST"])
def process_category_in_project(project_id):
    user = current_session_po_user()
    if user is None:
        return redirect("/")

    project = project_service.find_project_by_id(project_id)
    if project is None:
        flash("Projeto não localizado (ID: {}).".format(project_id))
        return redirect("/home")

    category_op = request.form['category_op']
    category_id = request.form['category_id']
    category_name = request.form['textCategoryName']

    category = Category(id=category_id, name=category_name)

    if category_op == 'add':
        try:
            category = project_service.add_new_category_to_project(category, project)
            if category is None or category.id == 0:
                flash("Falha ao incluir a Categoria '{}'. Contacte o Administrador.".format(category_name))
                return redirect('/home')
        except Exception as err:
            err_string = str(err)
            if "exist" in err_string:
                flash("Categoria '{}' já existente.".format(category_name))

    elif category_op == 'edit':
        try:
            category = project_service.change_category_data(category)
            if category is None or category.id == 0:
                flash("Falha ao alterar a Categoria '{}'. Contacte o Administrador.".format(category_name))
                return redirect('/home')
        except Exception as err:
            err_string = str(err)
            if "exist" in err_string:
                flash("Categoria '{}' já existente.".format(category_name))

    elif category_op == 'del':
        try:
            category_was_removed = project_service.remove_category_from_project(category, project)
            if not category_was_removed:
                flash("Não foi possível remover a Categoria '{}'. Contacte o Administrador.".format(category_name))
                return redirect('/home')
        except Exception as err:
            flash("Falha ao remover a Categoria '{}'. Contacte o Administrador.".format(category_name))
            return redirect('/home')

    return redirect('/projeto/{}'.format(project_id))


@app.route("/projeto/<project_id>/funcionalidade", methods=["POST"])
def process_feature_in_project(project_id):
    user = current_session_po_user()
    if user is None:
        return redirect("/")

    project = project_service.find_project_by_id(project_id)
    if project is None:
        flash("Projeto não localizado (ID: {}).".format(project_id))
        return redirect("/home")

    feature_op = request.form['feature_op']
    feature_id = request.form['feature_id']
    feature_name = request.form['textFeatureName']
    feature_status = request.form['selectFeatureStatus']
    feature_percent = request.form['textFeaturePercent']
    feature_date_str = request.form['textFeatureEndDate']
    feature_short_name = request.form['textFeatureShortName']

    category_id = request.form['feature_category_id']
    category = project_service.find_category_by_id(category_id)
    if category is None:
        flash("Categoria não localizada. Contacte o Administrador.")
        return redirect('/home')

    feature_end_date = None if feature_date_str == '' else datetime.strptime(feature_date_str, '%d/%m/%Y')

    feature = Feature(id=feature_id, short_name=feature_short_name, name=feature_name,
                      percent_done=feature_percent, estimated_end_date=feature_end_date,
                      status=feature_status)

    if feature_op == 'add':
        try:
            feature = project_service.add_new_feature_category(feature, category, project)
            if feature is None or feature.id == 0:
                flash("Falha ao incluir a Funcionalidade '{}'. Contacte o Administrador.".format(feature_short_name))
                return redirect('/home')
        except Exception as err:
            err_string = str(err)
            if "exist" in err_string:
                flash("Funcionalidade '{}' já existente.".format(feature_short_name))

    elif feature_op == 'edit':
        try:
            feature = project_service.change_feature_data(feature)
            if category is None or category.id == 0:
                flash("Falha ao alterar a Funcionalidade '{}'. Contacte o Administrador.".format(feature_short_name))
                return redirect('/home')
        except Exception as err:
            err_string = str(err)
            if "exist" in err_string:
                flash("Funcionalidade '{}' já existente.".format(feature_short_name))

    elif feature_op == 'del':
        try:
            feature_was_removed = project_service.remove_feature_from_category(feature, category, project)
            if not feature_was_removed:
                flash("Não foi possível remover a Funcionalidade '{}'. Contacte o Administrador.".format(
                    feature_short_name))
                return redirect('/home')
        except Exception as err:
            flash("Falha ao remover a Funcionalidade '{}'. Contacte o Administrador.".format(feature_short_name))
            return redirect('/home')

    return redirect('/projeto/{}'.format(project_id))


@app.route("/projeto/<project_id>/adicionar-usuario", methods=["POST"])
def add_user_to_project(project_id):
    user = current_session_po_user()
    if user is None:
        return redirect("/")

    project = project_service.find_project_by_id(project_id)
    if project is None:
        flash("Projeto não localizado (ID: {}).".format(project_id))
        return redirect("/home")

    user_email = request.form['textGuestEmail']
    user = user_service.find_user_by_email(user_email)
    if user is None:
        flash("O e-mail do convidado não está existe ({}).".format(user_email))
        return redirect('/projeto/{}'.format(project_id))

    user_granted = project_service.grant_access_to_user(user, project)
    if not user_granted:
        flash("O convidado já está com acesso concedido.")
        return redirect('/projeto/{}'.format(project_id))

    return redirect('/projeto/{}'.format(project_id))


@app.route("/projeto/<project_id>/remover-usuario", methods=["POST"])
def remove_user_to_project(project_id):
    user = current_session_po_user()
    if user is None:
        return redirect("/")

    project = project_service.find_project_by_id(project_id)
    if project is None:
        flash("Projeto não localizado (ID: {}).".format(project_id))
        return redirect("/home")

    user_id = request.form['user_id_to_revoke']
    user = user_service.find_user_by_id(user_id)
    if user is None:
        flash("O usuário convidado não foi localizado ({}).".format(user_id))
        return redirect('/projeto/{}'.format(project_id))

    user_revoked = project_service.revoke_access_from_user(user, project)
    if not user_revoked:
        flash("Falha ao remover o usuário selecionado ao projeto.")
        return redirect("/home")

    return redirect('/projeto/{}'.format(project_id))


@app.route("/dashboard/<project_id>", methods=["GET"])
def show_dashboard(project_id):
    
    user = current_session_po_user()
    print("/dashboard/<project_id>", user)
    if user is None:
        return redirect("/")

    project = project_service.find_project_by_id(project_id)
    if project is None:
        flash("Projeto não localizado (ID: {}).".format(project_id))
        return redirect("/home")

    project = project_service.load_project_by_id(project.id)
    granted_projects = list_all_granted_projects_for_user_in_current_session()

    return render_template("dashboard.html", granted_projects=granted_projects, project=project,
                           project_status=ProjectStatus, feature_status=FeatureStatus)


if __name__ == "__main__":
    app.run(debug=True)
