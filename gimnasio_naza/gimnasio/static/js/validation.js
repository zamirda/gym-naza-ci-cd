document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".modal").forEach((modal) => {
    const inputs = modal.querySelectorAll(".form-control, .form-select");

    inputs.forEach((input) => {
      input.addEventListener("input", () => validarCampo(input));

      input.addEventListener("change", () => validarCampo(input));
    });

    modal.addEventListener("hidden.bs.modal", () => {
      inputs.forEach((input) => {
        input.classList.remove("is-invalid", "is-valid");

        const errorDiv = document.getElementById(`error-${input.id}`);

        if (errorDiv) {
          errorDiv.remove();
        }
      });
    });
  });
});

function mostrarError(input, mensaje) {
  input.classList.remove("is-valid");
  input.classList.add("is-invalid");

  let errorDiv = document.getElementById(`error-${input.id}`);

  if (!errorDiv) {
    errorDiv = document.createElement("div");

    errorDiv.id = `error-${input.id}`;

    errorDiv.className =
      "invalid-feedback d-block text-start small fw-bold mt-1";

    errorDiv.style.fontSize = "11px";

    input.parentNode.appendChild(errorDiv);
  }

  errorDiv.textContent = mensaje;
}

function limpiarError(input) {
  input.classList.remove("is-invalid");

  input.classList.add("is-valid");

  const errorDiv = document.getElementById(`error-${input.id}`);

  if (errorDiv) {
    errorDiv.remove();
  }
}

function validarCampo(input) {
  const modal = input.closest(".modal");

  const id = input.id;

  // VALIDACIÓN PARA INPUT FILE
  if (input.type === "file") {
    if (modal.id === "modalElemento") {
      const archivo = input.files[0];

      if (!archivo) {
        mostrarError(input, "Debe seleccionar una imagen");

        return false;
      }

      const tiposPermitidos = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
      ];

      if (!tiposPermitidos.includes(archivo.type)) {
        mostrarError(input, "Solo se permiten imágenes");

        return false;
      }

      limpiarError(input);
      return true;
    }
  }

  const valor = input.value.trim();

  // CAMPOS VACÍOS
  if (valor === "") {
    let nombre = id.replace(/_/g, " ");

    mostrarError(input, `El campo "${nombre}" es obligatorio`);

    return false;
  }

  // =====================
  // VALIDACIONES USUARIO
  // =====================

  if (modal.id === "modalUsuario") {
    if (id === "documento" && !/^\d{7,10}$/.test(valor)) {
      mostrarError(input, "Debe tener entre 7 y 10 dígitos");

      return false;
    }

    if (
      (id === "nombre" || id === "apellido") &&
      !/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(valor)
    ) {
      mostrarError(input, "Solo se permiten letras");

      return false;
    }

    if (id === "correo" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
      mostrarError(input, "Correo electrónico inválido");

      return false;
    }

    if (id === "telefono" && !/^3\d{9}$/.test(valor)) {
      mostrarError(input, "Debe iniciar en 3 y tener 10 dígitos");

      return false;
    }

    if (id === "username" && valor.length < 4) {
      mostrarError(input, "Mínimo 4 caracteres");

      return false;
    }

    if (id === "password" && valor.length < 6) {
      mostrarError(input, "Mínimo 6 caracteres");

      return false;
    }

    if (id === "peso" && (Number(valor) < 30 || Number(valor) > 200)) {
      mostrarError(input, "Peso fuera de rango");

      return false;
    }

    if (id === "altura" && (Number(valor) < 100 || Number(valor) > 250)) {
      mostrarError(input, "Altura fuera de rango");

      return false;
    }

    if (id === "fecha_nacimiento") {
      const fecha = new Date(valor);

      const hoy = new Date();

      if (fecha >= hoy) {
        mostrarError(input, "Fecha inválida");

        return false;
      }
    }
  }

  // =====================
  // VALIDACIONES ELEMENTO
  // =====================

  if (modal.id === "modalElemento") {
    if (id === "serial" && valor.length < 3) {
      mostrarError(input, "El serial debe tener mínimo 3 caracteres");

      return false;
    }

    if (id === "Marca" && valor.length < 2) {
      mostrarError(input, "Ingrese una marca válida");

      return false;
    }

    if (id === "nombre_elemento" && valor.length < 3) {
      mostrarError(input, "Ingrese un nombre válido");

      return false;
    }

    if (id === "peso" && Number(valor) <= 0) {
      mostrarError(input, "Ingrese un peso válido");

      return false;
    }

    if (id === "cantidad" && Number(valor) <= 0) {
      mostrarError(input, "La cantidad debe ser mayor a cero");

      return false;
    }
    if (id === "categoria" && valor === "") {
      mostrarError(input, "Seleccione una categoría");
      console.log("Categoria" , valor);
      return false;
    }
  }

  limpiarError(input);

  return true;
}
function validarFormulario(modalId) {
  const modal = document.getElementById(modalId);

  const inputs = modal.querySelectorAll(".form-control, .form-select");

  let valido = true;

  inputs.forEach((input) => {
    if (!validarCampo(input)) {
      valido = false;
    }
  });

  return valido;
}
const passwordInput = document.getElementById("password");

const btnTogglePassword = document.getElementById("btnTogglePassword");

const iconPassword = document.getElementById("iconPassword");

if (btnTogglePassword) {
  btnTogglePassword.addEventListener("click", function () {
    const esPassword = passwordInput.type === "password";

    passwordInput.type = esPassword ? "text" : "password";

    iconPassword.className = esPassword ? "ri-eye-off-line" : "ri-eye-line";
  });
}
