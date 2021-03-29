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
        
        var offline_script = "{{offline_script}}";
        if (offline_script!=='{{offline_script}}') {
            // if python has given us an offline script to use:
            s.type = 'text/javascript';
            s.text = offline_script;
            document.body.appendChild( s ); // browser will try to load the new script tag
            oncompleted();
        }
        var script_url = "{{script_url}}";
        if (script_url !== '{{script_url}}') {
            s.setAttribute( 'src', script_url);
            s.onload=oncompleted;
            document.body.appendChild( s ); // browser will try to load the new script tag     
        }
    }) 
}
loadOSMD().then((OSMD)=>{
    console.log("loaded OSMD")
    var div_id = "{{DIV_ID}}";
        console.log(div_id)
    document.querySelector('#'+div_id).innerHTML = "";
    window.openSheetMusicDisplay = new OSMD.OpenSheetMusicDisplay(div_id);
    openSheetMusicDisplay
        .load("{{data}}") // this is replaced by the xml generated in python
        .then(
          function() {
            console.log("rendering data")
            openSheetMusicDisplay.render();
            // we could also remove this script tag to free up memory (would limit debugging though)
            // var me = document.currentScript;
            // me.parentNode.removeChild(me)
          }
        );
})
