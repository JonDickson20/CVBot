var haveEvents = 'GamepadEvent' in window;
var haveWebkitEvents = 'WebKitGamepadEvent' in window;
var controllers = {};
var rAF = window.mozRequestAnimationFrame ||
  window.webkitRequestAnimationFrame ||
  window.requesstAnimationFrame;
var previousValues = [];
var fire = false;
var axisDeadZone = 25;
var address = document.getElementById("address").value
console.log(address);
var socket = new WebSocket('ws://'+address+'00');


function connecthandler(e) {
  addgamepad(e.gamepad);
}
function addgamepad(gamepad) {
  controllers[gamepad.index] = gamepad; var d = document.createElement("div");
  d.setAttribute("id", "controller" + gamepad.index);
  var t = document.createElement("h1");
  t.appendChild(document.createTextNode("gamepad: " + gamepad.id));
  d.appendChild(t);
  var b = document.createElement("div");
  b.className = "buttons";
  for (var i=0; i<gamepad.buttons.length; i++) {
    var e = document.createElement("span");
    e.className = "button";
    //e.id = "b" + i;
    e.innerHTML = i;
    b.appendChild(e);
  }
  d.appendChild(b);
  var a = document.createElement("div");
  a.className = "axes";
  for (i=0; i<gamepad.axes.length; i++) {
    e = document.createElement("meter");
    e.className = "axis";
    //e.id = "a" + i;
    e.setAttribute("min", "-1");
    e.setAttribute("max", "1");
    e.setAttribute("value", "0");
    e.innerHTML = i;
    a.appendChild(e);
  }
  d.appendChild(a);
  document.getElementById("start_controller").style.display = "none";
  document.body.appendChild(d);
  rAF(updateStatus);
}

function disconnecthandler(e) {
  removegamepad(e.gamepad);
}

function removegamepad(gamepad) {
  var d = document.getElementById("controller" + gamepad.index);
  document.body.removeChild(d);
  delete controllers[gamepad.index];
}

function updateStatus() {    
  scangamepads();
  for (j in controllers) {
    var controller = controllers[j];
    var d = document.getElementById("controller" + j);
    var buttons = d.getElementsByClassName("button");
    for (var i=0; i<controller.buttons.length; i++) {      
      var b = buttons[i];
      var val = controller.buttons[i];
      var pressed = val == 1.0;
      var touched = false;
      if (typeof(val) == "object") {
        pressed = val.pressed;
        if ('touched' in val) {
          touched = val.touched;
        }
        val = val.value;
      }
      var pct = Math.round(val * 100);
      b.style.backgroundSize = pct  + "%" + " " + pct + "%";
      b.className = "button";
      if (pressed) {
        b.className += " pressed";        
      }
      if (touched) {
        b.className += " touched";        
      }
      
      if(previousValues['btn'+i] != pct){      
        //fire event here        
        console.log('button ' + i + ' at ' + pct);
        fire = true;       
        previousValues['time'] = new Date();
        //socket.send('button ' + i + ' at ' + pct);        
      }
      previousValues['btn'+i] = pct;
      
    }

    var axes = d.getElementsByClassName("axis");
    for (var i=0; i<controller.axes.length; i++) {      
      var a = axes[i];
      pct = Math.round(controller.axes[i] * 100);
      if (Math.abs(pct) < axisDeadZone) {
        pct = 0
      }      
      
      
      
      if(previousValues['time'] == undefined){
          //do nothing
      }else{
          now = new Date()
          keepAliveInterval = 1000
          
          elapsed = now - previousValues['time']          
          if(elapsed > keepAliveInterval) {
            previousValues['time'] = new Date();
            fire = true;
          }            
      }
      
      
      if(fire || previousValues['axis'+i] != pct){
        fire = false;
        previousValues['axis'+i] = pct;
        //fire event here        
        command_obj = diffSteer(previousValues['axis2'], previousValues['axis1'], 100, -100, 1);
        command_obj.riser = -previousValues['axis3'];
        command_obj.grabber = previousValues['btn7'];
        
        console.log(previousValues)
        console.log(command_obj)
                
        command_obj = JSON.stringify(command_obj)        
        socket.send(command_obj);
      }

      a.innerHTML = i + ": " + controller.axes[i].toFixed(4);
      a.setAttribute("value", controller.axes[i]);
    }
  }
  rAF(updateStatus);
}

function scangamepads() {
  var gamepads = navigator.getGamepads ? navigator.getGamepads() : (navigator.webkitGetGamepads ? navigator.webkitGetGamepads() : []);
  for (var i = 0; i < gamepads.length; i++) {
    if (gamepads[i] && (gamepads[i].index in controllers)) {
      controllers[gamepads[i].index] = gamepads[i];
    }
  }
}


function clamp(a,b,c){return Math.max(b,Math.min(c,a));}
diffSteer.axisFlip = -1;

function diffSteer(leftRightAxis, upDownAxis, maxAxis, minAxis, maxSpeed, axisFlip) {  
  var direction = 0;
  var leftMotorNoThrottleScale = 0;
  var leftMotorOutput = 0;
  var leftMotorScale = 0;
  var rightMotorNoThrottleTurnScale = 0;
  var rightMotorOutput = 0;
  var rightMotorScale = 0;
  var throttle;
  if(typeof axisFlip == 'undefined') {
    axisFlip = diffSteer.axisFlip;
  }
  if(typeof maxAxis == 'undefined') {
    maxAxis = diffSteer.maxAxis;
  }
  if(typeof minAxis == 'undefined') {
    minAxis = diffSteer.minAxis;
  }
  if(typeof maxSpeed == 'undefined') {
    maxSpeed = diffSteer.maxSpeed;
  }

  // Calculate Throttled Steering Motor values
  direction = leftRightAxis / maxAxis;

  // Turn with with throttle
  leftMotorScale = upDownAxis * (1 + direction);
  leftMotorScale = clamp(leftMotorScale, minAxis, maxAxis); // Govern Axis to Minimum and Maximum range

  rightMotorScale = upDownAxis * (1 - direction);
  rightMotorScale = clamp(rightMotorScale, minAxis, maxAxis); // Govern Axis to Minimum and Maximum range

  // Calculate No Throttle Steering Motors values (Turn with little to no throttle)
  throttle = 1 - Math.abs(upDownAxis / maxAxis); // Throttle inverse magnitude (1 = min, 0 = max)
  leftMotorNoThrottleScale = -leftRightAxis * throttle;
  rightMotorNoThrottleTurnScale = leftRightAxis * throttle;
  


  // Calculate final motor output values
  leftMotorOutput = (leftMotorScale + leftMotorNoThrottleScale) * axisFlip;
  leftMotorOutput = clamp(leftMotorOutput, minAxis, maxAxis);
  rightMotorOutput = (rightMotorScale + rightMotorNoThrottleTurnScale) * axisFlip;
  rightMotorOutput = clamp(rightMotorOutput, minAxis, maxAxis);

  //fix for reverse
  if(upDownAxis > 0){
    tmp = leftMotorOutput;
    leftMotorOutput = rightMotorOutput;
    rightMotorOutput = tmp;    
  }

  var obj = { left: Math.round(maxSpeed * leftMotorOutput), right: Math.round(maxSpeed * rightMotorOutput) };
  return obj;
}


if (haveEvents) {
  window.addEventListener("gamepadconnected", connecthandler);
  window.addEventListener("gamepaddisconnected", disconnecthandler);
} else if (haveWebkitEvents) {
  window.addEventListener("webkitgamepadconnected", connecthandler);
  window.addEventListener("webkitgamepaddisconnected", disconnecthandler);
} else {
  setInterval(scangamepads, 500);
}
