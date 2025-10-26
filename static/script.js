
$(document).ready(function() {
    $('#login-btn').click(function() {
        const username = $('#username').val();
        if (username) {
            login(username);
        }
    });

    $('#kill-btn').click(function() {
        const username = localStorage.getItem('username');
        if(username) {
            killTarget(username);
        }
    });

    function login(username) {
        localStorage.setItem('username', username);
        $.ajax({
            url: '/login',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ username: username }),
            success: function(data) {
                $('#login-section').hide();
                $('#game-section').show();
                $('#welcome-message').text('Welcome, ' + username + '!');
                updateGameView(data);
            }
        });
    }

    function getNewTarget(username) {
        $.ajax({
            url: '/target?username=' + username,
            type: 'GET',
            success: function(data) {
                updateGameView(data);
            }
        });
    }

    function killTarget(username) {
        $.ajax({
            url: '/kill',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ username: username }),
            success: function(data) {
                $('#score').text(data.score);
                getNewTarget(username);
            }
        });
    }

    function updateGameView(data) {
        $('#target-name').text(data.target);
        $('#target-word').text(data.word);
        $('#score').text(data.score);
    }
});
