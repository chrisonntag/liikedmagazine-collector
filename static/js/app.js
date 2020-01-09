document.onkeydown = checkKey;

function checkKey(e) {

    e = e || window.event;

    if (e.keyCode == '37') {
      document.getElementById('high').click();
    }
    else if (e.keyCode == '39') {
      document.getElementById('low').click();
    }

}