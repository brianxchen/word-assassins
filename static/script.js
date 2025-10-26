$(document).ready(function() {
    let refreshInterval;
    
    // Check for existing session on page load
    checkSession();
    
    // Load leaderboard immediately
    loadLeaderboard();

    $('#login-btn').click(function() {
        const username = $('#username').val();
        if (username) {
            login(username);
        }
    });

    $('#kill-btn').click(function() {
        killTarget();
    });

    // Add logout button functionality
    $('#logout-btn').click(function() {
        logout();
    });

    function checkSession() {
        $.ajax({
            url: '/session',
            type: 'GET',
            success: function(data) {
                // User has active session, show game view
                $('#login-section').hide();
                $('#game-section').show();
                $('#welcome-message').text('Welcome back, ' + data.username + '!');
                updateGameView(data);
                startAutoRefresh();
            },
            error: function() {
                // No active session, show login
                $('#login-section').show();
                $('#game-section').hide();
                stopAutoRefresh();
            }
        });
    }

    function login(username) {
        $.ajax({
            url: '/login',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ username: username }),
            success: function(data) {
                $('#login-section').hide();
                $('#game-section').show();
                $('#welcome-message').text('Welcome, ' + data.username + '!');
                updateGameView(data);
                startAutoRefresh();
            },
            error: function() {
                alert('Login failed. Please try again.');
            }
        });
    }

    function getNewTarget() {
        $.ajax({
            url: '/target',
            type: 'GET',
            success: function(data) {
                updateGameView(data);
            },
            error: function() {
                // If there's an error, user might not be logged in anymore
                checkSession();
            }
        });
    }

    function killTarget() {
        // Only allow killing if there's an actual target
        const targetName = $('#target-name').text();
        if (targetName === 'Waiting for more players...' || targetName === 'No word yet') {
            alert('You need to wait for more players to join!');
            return;
        }
        
        $.ajax({
            url: '/kill',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(data) {
                updateGameView(data);
                // Reload leaderboard after a kill
                loadLeaderboard();
            },
            error: function(xhr) {
                if (xhr.status === 400) {
                    alert('No target available to kill!');
                } else {
                    alert('Kill failed. Please try again.');
                }
            }
        });
    }

    function logout() {
        stopAutoRefresh();
        $.ajax({
            url: '/logout',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function() {
                $('#login-section').show();
                $('#game-section').hide();
                $('#username').val('');
                // Reload leaderboard after logout
                loadLeaderboard();
            },
            error: function() {
                // Even if logout fails, show login screen
                $('#login-section').show();
                $('#game-section').hide();
                $('#username').val('');
                loadLeaderboard();
            }
        });
    }

    function loadLeaderboard() {
        $.ajax({
            url: '/leaderboard',
            type: 'GET',
            success: function(data) {
                displayLeaderboard(data);
            },
            error: function() {
                $('#leaderboard-list').html('<p class="text-muted">Failed to load leaderboard</p>');
                $('#leaderboard-list-game').html('<p class="text-muted">Failed to load leaderboard</p>');
            }
        });
    }

    function displayLeaderboard(leaderboard) {
        let html = '';
        if (leaderboard.length === 0) {
            html = '<p class="text-muted">No players yet</p>';
        } else {
            html = '<ol class="list-group list-group-flush">';
            leaderboard.forEach(function(player, index) {
                const badgeClass = index === 0 ? 'badge-warning' : index === 1 ? 'badge-secondary' : 'badge-light';
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${player.username}
                    <span class="badge ${badgeClass}">${player.score}</span>
                </li>`;
            });
            html += '</ol>';
        }
        
        // Update both leaderboard displays
        $('#leaderboard-list').html(html);
        $('#leaderboard-list-game').html(html);
    }

    function updateGameView(data) {
        $('#target-name').text(data.target);
        $('#target-word').text(data.word);
        $('#score').text(data.score);
    }

    function startAutoRefresh() {
        // Refresh every 3 seconds to check for new players and update leaderboard
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        refreshInterval = setInterval(function() {
            getNewTarget();
            loadLeaderboard();
        }, 3000);
    }

    function stopAutoRefresh() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
});
