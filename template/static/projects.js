export class Projects{
    constructor(){
      this.lastProjectsControl = {'last': null, 'penultimate': null, 'antepenultimate': null};
    }

    setLastProjects(projectID){
      console.log("Antes de pegar o localstorage - this.lastProjectsControl['last']: " +this.lastProjectsControl['last']);
      
      if (localStorage.hasOwnProperty('last3projects')){
        console.log('Já tem projeto registrado');
        this.lastProjectsControl = JSON.parse(localStorage.getItem('last3projects'));
        this.lastProjectsControl['antepenultimate'] = this.lastProjectsControl['penultimate'];
        this.lastProjectsControl['penultimate'] = this.lastProjectsControl['last'];
      }
      this.lastProjectsControl['last'] = parseInt(projectID);
      console.log(this.lastProjectsControl);
      localStorage.setItem('last3projects', JSON.stringify(this.lastProjectsControl));
    }
  }