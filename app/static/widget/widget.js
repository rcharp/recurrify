(function(){
    var css = document.createElement('link');
    css.href = "embedjs.css";
    css.rel = "stylesheet";
    css.type = 'text/css';
    document.getElementsByTagName('head')[0].appendChild(css);

    $(document).ready(function() {
        $form = $("<form id='jsembed' action='/tokenize/' method='POST'></form>");
        $form.append("<label>Title</label>");
        $form.append("<br>")
        $form.append("<input type='text' class='title' name='title' value=''>");
        $form.append("<br>")
        $form.append("<label>Details</label>");
        $form.append("<br>")
        $form.append("<input type='text' class='details' name='details' value=''>");
        $form.append("<br>")
        $form.append("<button>Submit</button>");
        $(widget).html($form);


        $("#jsembed").submit(function(e) {
            e.preventDefault();
            var form = $(this);
            var serialized_form = form.serialize();
            serialized_form += "&username=" + localStorage.getItem("username");
            jwt_token = "";

            $.post({
                url: form.attr('action'),
                data: serialized_form
            })
            .always(function(data) {
                // Data was successfully encoded with JWT
                if(data.status == 200){
                    jwt_token = data.responseText;
                    $.post({
                        url: "/submit/",
                        data: "token=" + jwt_token
                    });
                } else {
                    // Failure behavior
                }
            });


        });
    });
});

/*
var code = '<div id="wishlist-widget" />\n<script src="https://code.jquery.com/jquery-3.5.1.min.js"\nintegrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0="\ncrossorigin="anonymous"><\/script>\n\n<script src="';
var widget = '(function(){var css = document.createElement(\'link\');css.href=\"embedjs.css\";css.rel=\"stylesheet\";css.type=\'text/css\';document.getElementsByTagName(\'head\')[0].appendChild(css);$(document).ready(function(){$form=$(\"<form id=\'jsembed\' action=\'/tokenize/\' method=\'POST\'></form>\");$form.append(\"<label>Title</label>\");$form.append(\"<br>\")$form.append(\"<input type=\'text\' class=\'title\' name=\'title\' value=\'\'>\");$form.append(\"<br>\")$form.append(\"<label>Details</label>\");$form.append(\"<br>\")$form.append(\"<input type=\'text\' class=\'details\' name=\'details\' value=\'\'>\");$form.append(\"<br>\")$form.append(\"<button>Submit</button>\");$(widget).html($form);$(\"#jsembed\").submit(function(e) {e.preventDefault();var form = $(this);var serialized_form = form.serialize();serialized_form += \"&username=\" + localStorage.getItem(\"username\");jwt_token = \"\";$.post({url: form.attr(\'action\'),data: serialized_form}).always(function(data) {// Data was successfully encoded with JWTif(data.status == 200){jwt_token = data.responseText;$.post({url: \"/submit/\",data: \"token=\" + jwt_token});} else {// Failure behavior}});});});});';

var render_code = '<script>\n' +
    '  Canny(\'render\', {\n' +
    '    boardToken: \'YOUR_BOARD_TOKEN\',\n' +
    '    basePath: null, // See step 2\n' +
    '    ssoToken: null, // See step 3\n' +
    '  });\n' +
    '</script>';
*/
