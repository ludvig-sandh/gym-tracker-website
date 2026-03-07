window.onload = function() {
    var today = new Date();
    var date = today.getDate();
    var month = today.getMonth() + 1;
    if (date == 1 && month == 4) {
        const elem = document.getElementById("bg_image");
        elem.style.opacity = "1";
    }

    var weekDay = today.getDay();
    if (weekDay == 1) {
        // Ha kvar default färg: #23a6d5
        document.body.style.backgroundColor = "#23a6d5";
    }else if (weekDay == 2) {
        document.body.style.backgroundColor = "#1e96c2";
    }else if (weekDay == 3) {
        document.body.style.backgroundColor = "#237cd5";
    }else if (weekDay == 4) {
        document.body.style.backgroundColor = "#1b63b5";
    }else if (weekDay == 5) {
        document.body.style.backgroundColor = "#0f5eb9";
    }else if (weekDay == 6) {
        document.body.style.backgroundColor = "#0f58ac";
    }else if (weekDay == 7) {
        document.body.style.backgroundColor = "#0f58ac";
    }
};