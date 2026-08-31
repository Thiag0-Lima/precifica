// ===== Modal de Insumo =====
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add("open");
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove("open");
}

// Fecha modal ao clicar fora
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.classList.remove("open");
    }
});

// ===== Formulário de Receita - adicionar linha de ingrediente =====
function addItemRow() {
    const tbody = document.getElementById("itens-body");
    if (!tbody) return;

    const firstSelect = tbody.querySelector("select[name='insumo_id']");
    if (!firstSelect) return;

    const optionsHtml = firstSelect.innerHTML;

    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>
            <select name="insumo_id" required>
                ${optionsHtml}
            </select>
        </td>
        <td>
            <input type="number" name="quantidade" step="0.01" min="0.01" required placeholder="Qtd">
        </td>
        <td>
            <select name="unidade">
                <option value="g">g</option>
                <option value="kg">kg</option>
                <option value="ml">ml</option>
                <option value="L">L</option>
                <option value="un">un</option>
            </select>
        </td>
        <td>
            <button type="button" class="btn-icon" onclick="this.closest('tr').remove()">🗑</button>
        </td>
    `;
    tbody.appendChild(tr);
}

// ===== Confirmação de exclusão =====
function confirmDelete(form) {
    if (confirm("Tem certeza que deseja excluir?")) {
        form.submit();
    }
    return false;
}
