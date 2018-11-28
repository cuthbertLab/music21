console.log("loadOSMD()");
function loadOSMD() { 
    return new Promise(function(resolve, reject){

        if (window.opensheetmusicdisplay) {
            console.log("already loaded")
            return resolve(window.opensheetmusicdisplay)
        }
        console.log("loading osmd for the first time")
        // OSMD script has a 'define' call which conflicts with requirejs
        var _define = window.define // save the define object 
        window.define = undefined // now the loaded script will ignore requirejs
        var s = document.createElement( 'script' );
        function oncompleted(){
            window.define = _define
            console.log("loaded OSMD for the first time",opensheetmusicdisplay)
            resolve(opensheetmusicdisplay);
        };
        {{script_command}}
        
    }) 
}
loadOSMD().then((OSMD)=>{
    console.log("loaded OSMD",OSMD)
    var div_id = "{{DIV_ID}}";
        console.log(div_id)
    document.querySelector('#'+div_id).innerHTML = "";
    window.openSheetMusicDisplay = new OSMD.OpenSheetMusicDisplay(div_id);
    openSheetMusicDisplay
        .load({{data}})
        .then(
          function() {
            console.log("rendering data")
            openSheetMusicDisplay.render();
          }
        );
})