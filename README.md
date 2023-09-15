# Dashboard
Dashboard de Acompanhamento do Desenvolvimento de Software baseado em Metodologia Ágil


# Instalação necessária
## Variável de ambiente para o Python
### O Linux já vem com o python3-venv
$ sudo apt-get install python3-venv

### Definir a variável de ambiente (padrão 'venv')
$ python3 -m venv venv

### Ativar a variável de ambiente
$ source venv/bin/active 

## Instalação do Flask
(venv) $ pip install flask

# Princípios usados no Projeto Web em Python com Flask
- Referências: 
-- https://www.youtube.com/watch?v=GE6asEjTFv8&ab_channel=C%C3%B3digoFonteTV
-- https://engsoftmoderna.info/artigos/ddd.html

# Variáveis de ambiente para o Flask  
## Ambiente de DEV
FLASK_ENV=development flask run 

# Instalação de Extensões do Flask
## Flask Bootstrap
(venv) $ pip install flask-bootstrap


## Flask DynaConf
(venv) $ pip install dynaconf

## Flask Admin
(venv) $ pip install flask-admin 

## Flask SQLAlchemy
(venv) $ pip install -U Flask-SQLAlchemy

## Flask .env (dotenv)
(venv) $ pip install python-dotenv

## Python Mysql
(venv) $pip install mysql-connector-python