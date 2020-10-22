function ShowDropdown(id) {
    var dropdown = document.getElementById(id);
    if (dropdown.classList.contains('opacity-0')){
        dropdown.classList.remove('opacity-0');
        dropdown.classList.remove('scale-95');
        dropdown.classList.add('opacity-100');
        dropdown.classList.add('scale-100');

        dropdown.style.display = '';
    }
    else {
        dropdown.classList.remove('opacity-100');
        dropdown.classList.remove('scale-100');
        dropdown.classList.add('opacity-0');
        dropdown.classList.add('scale-95');

        dropdown.style.display = 'none';
    }
}

function ShowLogin(action, feedback_id){
    if ('{{ demo }}' === 'True'){
        return false;
    }

    var login_overlay = document.getElementById('login-overlay-' + action);
    login_overlay.style.display = '';
    document.getElementById('feedback-id').value = feedback_id;

    var login_overlay_modal = document.getElementById('login-overlay-modal');

    if (login_overlay_modal !== null){
        login_overlay_modal.addEventListener("click", function () {
            login_overlay.style.display = 'none';
        }, false);
    }
}

function Vote(feedback_id, logged_in) {
    if (logged_in){
        var url = ReplaceSubdomain("{{ url_for('user.update_vote', subdomain='DUMMY_VALUE') }}");
        $.ajax({
            url: url,
            type: 'POST',
            beforeSend: UpdateVote(feedback_id),
            data: {'feedback_id': feedback_id, 'user_id': '{{ current_user.id }}'},
            success: function (response) {
                if ('success' in response){
                    //window.location.href = "{{ url_for('user.dashboard') }}";
                }
            },
            error: function (xhr) {
            }
        });
    }
    else{
        ShowLogin('vote', feedback_id);
    }

}

function UpdateVote(feedback_id) {
    var votes = document.getElementById(feedback_id + '-votes').innerText;
    var count = parseInt(votes);

    if (document.getElementById('votes-' + feedback_id).classList.contains('text-indigo-600')){
        document.getElementById(feedback_id + '-votes').innerText = String(count + 1);
        document.getElementById('votes-' + feedback_id).classList.remove('text-indigo-600');
        document.getElementById('votes-' + feedback_id).classList.add('text-green-400');
    }
    else{
        document.getElementById(feedback_id + '-votes').innerText = String(count - 1);
        document.getElementById('votes-' + feedback_id).classList.remove('text-green-400');
        document.getElementById('votes-' + feedback_id).classList.add('text-indigo-600');
    }

    if ('{{ demo }}' === 'True'){
        return false;
    }
}

function FilterByStatus(){
    // Uncheck all other checkboxes
    var otherCheckboxes = document.querySelectorAll('.filter-checkbox');
    for (var i = 0; i < otherCheckboxes.length; i++){
        otherCheckboxes[i].checked = false;
    }

    // Get the checked status boxes
    var checked = document.querySelectorAll('.status-checkbox:checked');
    var items = document.getElementsByClassName('feedback-item');

    // If no boxes are checked, show all feedback
    if (checked.length === 0){
        for (var i = 0; i < items.length; i++){
            items[i].style.display = '';
        }
        return;
    }

    // Otherwise, only show feedback that correspond to checked statuses
    var statuses = [];
    for (var i = 0; i< checked.length; i++){
        statuses.push(checked[i].name);
    }

    for (var i = 0; i < items.length; i++){
        var status = items[i].getAttribute('data-status');
        if (!statuses.includes(status)){
            items[i].style.display = 'none';
        }else {
            items[i].style.display = '';
        }
    }
}

function FilterByOther(){
    // Uncheck all status checkboxes
    var statusCheckboxes = document.querySelectorAll('.status-checkbox');
    for (var i = 0; i < statusCheckboxes.length; i++){
        statusCheckboxes[i].checked = false;
    }

    // Get the checked boxes for the 'other' category
    var checked = document.querySelectorAll('.filter-checkbox:checked');
    var items = document.getElementsByClassName('feedback-item');

    // If no boxes are checked, show all feedback
    if (checked.length === 0){
        for (var i = 0; i < items.length; i++){
            items[i].style.display = '';
        }
        return;
    }

    // Otherwise, only show feedback that correspond to checked filters
    var filters = [];
    for (var i = 0; i< checked.length; i++){
        filters.push(checked[i].name);
    }

    for (var i = 0; i < items.length; i++){
        var submitted = items[i].getAttribute('data-submitted');
        var voted = items[i].getAttribute('data-voted');
        var show = false;

        if (filters.includes('submitted')){
            if (submitted === 'true'){
                show = true;
            }
        }
        if (filters.includes('voted')){
            if (voted === 'true'){
                show = true;
            }
        }

        if (show){
            items[i].style.display = '';
        }
        else {
            items[i].style.display = 'none';
        }
    }
}

function SearchFeedback(e){
    var input = '';

    input += e.value;

    var items = document.getElementsByClassName('feedback-item');
    document.getElementById('search-term').innerText = input;

    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if(item.textContent.toLowerCase().includes(input.toLowerCase()) === false){
            item.style.display = 'none';
        }
        else {
            item.style.display = '';
        }
    }

    if (input){
        document.getElementById('search-results').style.display = '';
    }
    else {
        document.getElementById('search-results').style.display = 'none';
    }
}

function ReplaceSubdomain(url){
    var new_url = url.replace(/DUMMY_VALUE/, '{{ subdomain }}').toLowerCase();
    return new_url;
}

function TogglePrivacy(){
    var public_toggle = document.getElementById('public-toggle');
    var private_toggle = document.getElementById('private-toggle');
    var privacy;

    if (public_toggle.classList.contains('bg-indigo-600')){
        public_toggle.classList.remove('bg-indigo-600');
        public_toggle.classList.add('bg-gray-200');

        private_toggle.classList.remove('translate-x-5');
        private_toggle.classList.add('translate-x-0');

        privacy = false;
    }else{
        public_toggle.classList.remove('bg-gray-200');
        public_toggle.classList.add('bg-indigo-600');

        private_toggle.classList.remove('translate-x-0');
        private_toggle.classList.add('translate-x-5');

        privacy = true;
    }

    SetPrivacy(privacy, '{{ domain.domain_id }}')
}

function SetPrivacy(privacy, domain_id){
    var url = "{{ url_for('user.set_domain_privacy') }}";
    $.ajax({
        url: url,
        type: 'POST',
        data: {'domain_id': domain_id, 'privacy': privacy},
        success: function (response) {
        },
        error: function (xhr) {
        }
    });
}

function UpdateStatus(sel){
    document.getElementById('status').value = sel.id;
    document.getElementById('selected-status').innerText = sel.getAttribute('data-status-name');
}

function GetComments(feedback_id){
    var url = "{{ url_for('user.get_comments') }}";

    var user_id = null;
    if ('{{ current_user.is_authenticated }}' === 'True'){
        user_id = '{{ current_user.id }}';
    }
    $.ajax({
        url: url,
        type: 'POST',
        data: {'feedback_id': feedback_id, 'user_id': user_id},
        success: function (response) {
            InitializeComments(response['comments']);
        },
        error: function (xhr) {
        }
    });
}

// Initialize comments
function InitializeComments(comments){
    var user_id = null;
    var readOnly = false;
    if ('{{ current_user.is_authenticated }}' === 'True'){
        user_id = '{{ current_user.id }}';
    }else{
        readOnly = true;
    }

    $('#comments-container').comments({
        //profilePictureURL: "{{ url_for('static', filename='icons/user.png') }}",
        enableUpvoting: false,
        postCommentOnEnter: true,
        readOnly: readOnly,
        getComments: function(success, error) {
            success(comments);
        },
        postComment: function(commentJSON, success, error) {
            var data = Object.assign(commentJSON, {'feedback_id': '{{ feedback.feedback_id }}', 'user_id': user_id});
            $.ajax({
                type: 'POST',
                url:  "{{ url_for('user.add_comment') }}",
                data: data,
                beforeSend: success(commentJSON),
                success: function(comment) {
                },
                error: error
            });
        },
        putComment: function(commentJSON, success, error) {
            var data = Object.assign(commentJSON, {'feedback_id': '{{ feedback.feedback_id }}', 'user_id': user_id});
            $.ajax({
                type: 'POST',
                url:  "{{ url_for('user.update_comment') }}",
                data: data,
                beforeSend: success(commentJSON),
                success: function(comment) {
                },
                error: error
            });
        }
    });
}

function ShowLogin(action, feedback_id){

    // Do nothing if we are on the demo dashboard
    if ('{{ demo }}' === 'True'){
        return false;
    }

    // Show the modal
    var login_overlay = document.getElementById('login-overlay-' + action);
    login_overlay.style.display = '';

    // Set the feedback id
    document.getElementById('feedback-id').value = feedback_id;

    // Set the event listener to close the model when clicking outside of the box
    var login_overlay_modal = document.getElementById('login-overlay-modal');
    if (login_overlay_modal !== null){
        login_overlay_modal.addEventListener("click", function () {
            login_overlay.style.display = 'none';
        }, false);
    }
}