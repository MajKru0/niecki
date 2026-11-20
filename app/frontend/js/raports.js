import { getCLC } from "./layers.js";
const API = "/api";
var clicked = 0;
var radioDis  = true;
var copyFilterClass;
var form1;
export var vectorLayersNames = [];
var isGenReady = false;
copyFilterClass = document.getElementsByClassName('filter-items')[0].cloneNode(true);
copyFilterClass.setAttribute('class', 'raport-filter-items');
const clcF = copyFilterClass.querySelector("#filter-clc");
clcF.setAttribute('name', 'chosenCLC');
//const info = new Control({position: "topright"});
L.Control.Button = L.Control.extend({
    options: {
        position: 'topright'
    },
    onAdd: function(map){
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    console.log('click');
    this._div.innerHTML = `<i class="fa fa-download fa-2x" aria-hidden="true"></i>`;
    this._div.addEventListener('click', () => {
        console.log('clickclick click');
        if(clicked > 0){
            clicked = 0;
            generator.remove();
            return;
        }else{
            clicked = 1; 
        } 
        console.log("aaaa");
        this.update();
        

        
        
        
    });
    L.DomEvent.disableClickPropagation(this._div);
    return this._div;
},
    update: function () {
        console.log("23");
            if(clicked == 0){
                clicked = 0;
                console.log("oopsie");
                return;
            } 
        generator.addTo(window.map);
        document.getElementById('filtergr').appendChild(copyFilterClass);
        clcF.insertAdjacentHTML('afterend', '<small class="smallErr"></small>');
        getCLC(false);
        radioCheck();
        form1 = document.getElementById('raport');
        form1.addEventListener('submit', (event) => {
            event.preventDefault();
             ////////////EGMS/////////////
            console.log(document.forms)
            const f = event.target;
            const formData = new FormData(f);
            formData.append("chosenLayers", vectorLayersNames.map((v, k) => v.layerN));
            const isValidated = validateRaport(formData);
            if(!isValidated) return;
            generateReport(formData);

        });
            
}
});
export var info = new L.Control.Button();


L.Control.CustomControl = L.Control.extend({
    options: {
        position: 'topright'
    },
    onAdd: function(){
    this._div = L.DomUtil.create('div', 'generation-form'); // create a div with a class "generation-form"
    console.log('show form'); //last
    

    this._div.innerHTML = `<h4>Generate Raport</h4><form id="raport"><fieldset id="radiogr">
        <input type="radio" id="cmv" name="bounds" value="0" checked>
        <label for="cmv">Current Map View</label><br>
        <input type="radio" id="coord" name="bounds" value="1">
        <label for="coord">Input Own Coordinates</label></fieldset><br><p id="pepe"></p>
        <fieldset id="filtergr">
        </fieldset><br>` +  (vectorLayersNames.length>0 ? `
        <button id="genBtn" type="submit">Generate Raport</button>` : `<button id="genBtn" type="submit" disabled>Generate Raport
        </button>`)+
        `</form>`;
    L.DomEvent.disableClickPropagation(this._div);
    L.DomEvent.on(this._div, 'wheel', L.DomEvent.stopPropagation);

    return this._div;
    },
    update: function(resul){
        //radioCheck2();
        console.log("abhdbejcbewknck", resul);
        const subject = document.querySelector("#pepe");
        subject.innerHTML = `<fieldset id="coordinatesgr">` + (resul ? `
            P1 Longitude: <input type="number" id="lon1" min="0" max="180" step=".00001" name="coords" disabled >
            P1 Latitude: <input type="number" id="lat1" min="0" max="180" step=".0001" name="coords" disabled >
            P2 Longitude:  <input type="number" id="lon2" min="0" max="180" step=".0001" name="coords" disabled >
            P2 Latitude:  <input type="number" id="lat2" min="0" max="180" step=".0001" name="coords" disabled >
            P3 Longitude:  <input type="number" id="lon3" min="0" max="180" step=".0001" name="coords" disabled >
            P3 Latitude:  <input type="number" id="lat3" min="0" max="180" step=".0001" name="coords" disabled >
            P4 Longitude:  <input type="number" id="lon4" min="0" max="180" step=".0001" name="coords" disabled >
            P4 Latitude:  <input type="number" id="lat4" min="0" max="180" step=".0001" name="coords" disabled ></fieldset><br>` :  `
            P1 Longitude:  <input type="number" id="lon1" min="0" max="180" step=".0001" name="coords" required>
            P1 Latitude:  <input type="number" id="lat1" min="0" max="180" step=".0001" name="coords" required>
            P2 Longitude: <input type="number" id="lon2" min="0" max="180" step=".0001" name="coords" required>
            P2 Latitude: <input type="number" id="lat2" min="0" max="180" step=".0001" name="coords" required>
            P3 Longitude:  <input type="number" id="lon3" min="0" max="180" step=".0001" name="coords" required>
            P3 Latitude:  <input type="number" id="lat3" min="0" max="180" step=".0001" name="coords" required>
            P4 Longitude:  <input type="number" id="lon4" min="0" max="180" step=".0001" name="coords">
            P4 Latitude:  <input type="number" id="lat4" min="0" max="180" step=".0001" name="coords">
            </fieldset><br>`); //TODO: flytobounds
            
           // subject.insertAdjacentHTML('beforebegin', trustedHtml);
           L.DomEvent.disableClickPropagation(this._div);
            L.DomEvent.on(this._div, 'wheel', L.DomEvent.stopPropagation);



    radioCheck();
    
    }
});
var generator =  new L.Control.CustomControl();
//const r2 = document.querySelector("#coord");
//const r1 = document.querySelector("#cmv");
function radioCheck(){
    const r2 = document.querySelector("#coord");
    const r1 = document.querySelector("#cmv");
    r1.addEventListener("change", (event) => {
        radioDis=true;
        generator.update(radioDis);
        console.log(copyFilterClass.className);

     //  document.getElementById('filtergr').appendChild(copyFilterClass);
     //  getCLC(false)

});
    r2.addEventListener("change", (event) => {
        radioDis=false;
        generator.update(radioDis);
            console.log(copyFilterClass.className);

      // document.getElementById('filtergr').appendChild(copyFilterClass);
     //  getCLC(false)
});

}
export function getLayers2raport(isReady, layersOn){
    if(!isReady) return;
    isGenReady = isReady;
    console.log(layersOn);
    vectorLayersNames.push(layersOn);
    
    window.map.on("overlayremove", e =>{
        console.log("bbb", e.name);
    vectorLayersNames = vectorLayersNames.filter(x => x.label != e.name);
    if(vectorLayersNames.length>0){
    console.log("can generate report1", ...vectorLayersNames);
}else{
    isGenReady = false;
    generator.remove();
    console.log("12");
    info.update();
    console.log("cannot generate raport, choose layers1")
}
});
if(vectorLayersNames.length>0){
    console.log("can generate report", ...vectorLayersNames);
}else{
    isGenReady = false;
    console.log("cannot generate raport, choose layers")
}
if(isGenReady){
    info.update();
}
}

function generateReport(forms){
    //Layers//
    const selectedLayers = forms.getAll("chosenLayers");

    //RADIO//
    const selectedRadio = forms.get("bounds");

    let arrStr = "";
    selectedLayers.forEach((el, k) => arrStr = arrStr+"'"+el+": "+ k +"',");
    console.log("czekammm", arrStr);
    
    //BOUNDS//
    let selectedBounds = "";
    if(selectedRadio=="1"){
        //TODO: check if in pairs
       selectedBounds = forms.getAll("coords").join(",");
    }else{
        selectedBounds =(window.map.getBounds().toBBoxString());
    }
    
    //FILTERS//
    var filterObj = {min: -90, max: 30, clc: []};
    filterObj.min = form1.elements['filter-velocity-min'].value;
    filterObj.max = form1.elements['filter-velocity-max'].value;
    filterObj.clc = forms.getAll("chosenCLC");
    
    console.log("bbox: ", selectedBounds);

}

function validateRaport(forms){
   let timeoutId;
   if(timeoutId){
        clearTimeout(timeoutId);
    }
    const showError = (input, message) => {
        
    // add the error class
    form1.classList.remove('success');
    form1.classList.add('error');

    // show the error message
    
   // input.insertAdjacentHTML('afterend', '<small class="smallErr"></small>');
    const error = input.querySelector('.smallErr');
    error.innerHTML = message;
    console.log(message);
    setTimeout(() => {error.innerHTML = ''}, 50000);
    };

    const showSuccess = (input) => {

        // remove the error class
        form1.classList.remove('error');
        form1.classList.add('success');

        // hide the error message
        //add tag
        console.log("success");
        const error = input.querySelector('.smallErr');
        error.innerHTML = '';
    }
    const checkClc = () => {
            let valid = false;
            const clcArr = forms.getAll("chosenCLC");
            if(clcArr.includes('100') && clcArr.some(el => el != '100')){
                showError(form1, 'You cannot choose option "ALL" with other options. <br> Deselect "ALL" or all the other options.');
            }else{
                showSuccess(form1);
                valid=true;
            }
            return valid;
    }


    return checkClc(); //po dodaniu kolejnych rób &&
}
