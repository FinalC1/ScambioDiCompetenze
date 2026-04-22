function doLogin() {
      var email = document.getElementById("input-username").value.trim();
      var password = document.querySelector('input[type="password"]').value;
      
      if (!email || !password) { 
        alert("Inserisci email e password.");
        return; 
      }
      
      fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email, password: password})
      })
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          window.location.href = '/dashboard';
        } else {
          alert('Errore: ' + (data.error || 'Login fallito'));
        }
      })
      .catch(err => {
        console.error('Errore:', err);
        alert('Errore di connessione');
      });
    }
    
    document.addEventListener("DOMContentLoaded", function(){
      document.getElementById("input-username").addEventListener("keydown", function(e){
        if (e.key === "Enter") doLogin();
      });
    });