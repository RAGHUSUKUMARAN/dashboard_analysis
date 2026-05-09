setInterval(function () {
    var el = document.getElementById("logs_container");
    if (el) {
        el.scrollTop = el.scrollHeight;
    }
}, 500);