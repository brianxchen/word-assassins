$(document).ready(function() {
    let refreshInterval;
    let isAdmin = false;
    
    // Check for existing session on page load
    checkSession();
    
    // Load leaderboard and kill log immediately
    loadLeaderboard();
    loadKillLog();

    $('#login-btn').click(function() {
        const username = $('#username').val();
        if (username) {
            login(username);
        }
    });

    $('#kill-btn').click(function() {
        killTarget();
    });

    $('#logout-btn').click(function() {
        logout();
    });

    // Admin button handlers
    $('#reset-game-btn').click(function() {
        if (confirm('Are you sure you want to reset the entire game? This will remove all players, scores, and kill log.')) {
            resetGame();
        }
    });

    $('#remove-player-btn').click(function() {
        const username = $('#remove-username').val();
        if (username && confirm(`Are you sure you want to remove player "${username}"?`)) {
            removePlayer(username);
        }
    });

    $('#add-score-btn').click(function() {
        const username = $('#score-username').val();
        const points = parseInt($('#score-points').val()) || 1;
        if (username) {
            addScore(username, points);
        }
    });

    $('#refresh-admin-btn').click(function() {
        loadLeaderboard();
        loadKillLog();
    });

    $('#admin-logout-btn').click(function() {
        logout();
    });

    function checkSession() {
        $.ajax({
            url: '/session',
            type: 'GET',
            success: function(data) {
                if (data.is_admin) {
                    // Show admin panel
                    $('#login-section').hide();
                    $('#game-section').hide();
                    $('#admin-section').show();
                    isAdmin = true;
                    startAutoRefresh();
                } else {
                    // User has active session, show game view
                    $('#login-section').hide();
                    $('#game-section').show();
                    $('#admin-section').hide();
                    $('#welcome-message').text('Welcome back, ' + data.username + '!');
                    updateGameView(data);
                    startAutoRefresh();
                }
            },
            error: function() {
                // No active session, show login
                $('#login-section').show();
                $('#game-section').hide();
                $('#admin-section').hide();
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
                if (data.is_admin) {
                    // Show admin panel
                    $('#login-section').hide();
                    $('#game-section').hide();
                    $('#admin-section').show();
                    isAdmin = true;
                } else {
                    // Show regular game view
                    $('#login-section').hide();
                    $('#game-section').show();
                    $('#admin-section').hide();
                    $('#welcome-message').text('Welcome, ' + data.username + '!');
                    updateGameView(data);
                }
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
                if (data.is_admin) {
                    // Keep showing admin panel
                    return;
                }
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
                // Reload leaderboard and kill log after a kill
                loadLeaderboard();
                loadKillLog();
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
                $('#admin-section').hide();
                $('#username').val('');
                isAdmin = false;
                // Reload leaderboard and kill log after logout
                loadLeaderboard();
                loadKillLog();
            },
            error: function() {
                // Even if logout fails, show login screen
                $('#login-section').show();
                $('#game-section').hide();
                $('#admin-section').hide();
                $('#username').val('');
                isAdmin = false;
                loadLeaderboard();
                loadKillLog();
            }
        });
    }

    // Admin functions
    function resetGame() {
        $.ajax({
            url: '/admin/reset',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(data) {
                alert('Game reset successfully!');
                loadLeaderboard();
                loadKillLog();
            },
            error: function() {
                alert('Failed to reset game.');
            }
        });
    }

    function removePlayer(username) {
        $.ajax({
            url: '/admin/remove-player',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ username: username }),
            success: function(data) {
                alert(`Player ${username} removed successfully!`);
                $('#remove-username').val('');
                loadLeaderboard();
                loadKillLog();
            },
            error: function() {
                alert('Failed to remove player.');
            }
        });
    }

    function addScore(username, points) {
        $.ajax({
            url: '/admin/add-score',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ username: username, points: points }),
            success: function(data) {
                alert(`Added ${points} points to ${username}!`);
                $('#score-username').val('');
                $('#score-points').val('1');
                loadLeaderboard();
            },
            error: function() {
                alert('Failed to add score.');
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
                $('#admin-leaderboard').html('<p class="text-muted">Failed to load leaderboard</p>');
            }
        });
    }

    function loadKillLog() {
        $.ajax({
            url: '/kill-log',
            type: 'GET',
            success: function(data) {
                displayKillLog(data);
            },
            error: function() {
                $('#kill-log-list').html('<p class="text-muted">Failed to load kill log</p>');
                $('#kill-log-list-game').html('<p class="text-muted">Failed to load kill log</p>');
                $('#admin-kill-log').html('<p class="text-muted">Failed to load kill log</p>');
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
        
        // Update all leaderboard displays
        $('#leaderboard-list').html(html);
        $('#leaderboard-list-game').html(html);
        $('#admin-leaderboard').html(html);
    }

    function displayKillLog(killLog) {
        let html = '';
        if (killLog.length === 0) {
            html = '<p class="text-muted">No kills yet</p>';
        } else {
            html = '<div class="kill-log-entries">';
            killLog.forEach(function(kill) {
                const timeStr = new Date(kill.timestamp).toLocaleTimeString();
                html += `<div class="kill-entry">
                    <strong>${kill.killer}</strong> killed <strong>${kill.target}</strong>
                    <br><small class="text-muted">with "${kill.word}" at ${timeStr}</small>
                </div>`;
            });
            html += '</div>';
        }
        
        // Update all kill log displays
        $('#kill-log-list').html(html);
        $('#kill-log-list-game').html(html);
        $('#admin-kill-log').html(html);
    }

    function updateGameView(data) {
        $('#target-name').text(data.target);
        $('#target-word').text(data.word);
        $('#score').text(data.score);
    }

    function startAutoRefresh() {
        // Refresh every 3 seconds to check for new players and update displays
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        refreshInterval = setInterval(function() {
            if (!isAdmin) {
                getNewTarget();
            }
            loadLeaderboard();
            loadKillLog();
        }, 3000);
    }

    function stopAutoRefresh() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
});
