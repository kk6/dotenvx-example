document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('search-form');
  if (!form) return;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var username = document.getElementById('username-input').value.trim();
    if (username) {
      window.location.href = '/profile/' + encodeURIComponent(username);
    }
  });
});
