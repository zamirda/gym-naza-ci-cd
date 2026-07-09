document.getElementById("loginForm").addEventListener("submit", function(e) {
  e.preventDefault();

  const correoLogin = document.getElementById("correoLogin").value;
  const passwordLogin = document.getElementById("passwordLogin").value;
  const rol = document.getElementById("rol").value;

  let usuarios = JSON.parse(localStorage.getItem("usuarios")) || [];

  // Clave única del admin
  const adminClave = "Admin12345*"; 

  // 🔹 ADMIN
  if (rol === "admin") {
    if (correoLogin === "admin@insidebox.com" && passwordLogin === adminClave) {
      localStorage.setItem("usuarioActivo", JSON.stringify({ nombre: "Administrador", rol: "admin" }));
      alert("Bienvenido Administrador");
      window.location.href = "menu2.html"; //  usa el mismo menú
      return;
    } else {
      alert("Clave de administrador incorrecta");
      return;
    }
  }

  // 🔹 USUARIO NORMAL
  const usuarioValido = usuarios.find(
    u => u.correo === correoLogin && u.password === passwordLogin
  );

  if (usuarioValido) {
    localStorage.setItem("usuarioActivo", JSON.stringify(usuarioValido));
    alert("Inicio de sesión exitoso.");
    window.location.href = "menu.html"; // 👈 mismo archivo
  } else {
    alert("Correo o contraseña incorrectos.");
  }
});
//mostrar/ocultar contraseña
function togglePassword(id, el) {
  const input = document.getElementById(id);

  if (input.type === "password") {
    input.type = "text";
    el.classList.remove("fa-eye");
    el.classList.add("fa-eye-slash");
  } else {
    input.type = "password";
    el.classList.remove("fa-eye-slash");
    el.classList.add("fa-eye");
  }
}
