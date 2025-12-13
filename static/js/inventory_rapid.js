// inventory_rapid.js

document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('inventoryTableBody');
    const searchInput = document.getElementById('search');
    const categoryFilter = document.getElementById('categoryFilter');
    const exportBtn = document.getElementById('exportInventory');
    const adjustModal = document.getElementById('adjustModal');
    const adjustForm = document.getElementById('adjustForm');
    const adjustProductId = document.getElementById('adjustProductId');
    const newStockInput = document.getElementById('newStock');
    const cancelAdjust = document.getElementById('cancelAdjust');

    let products = [];
    let categories = [];

    function fetchInventory() {
        axios.get('/inventory/api/products/')
            .then(res => {
                products = res.data.products;
                renderTable();
                populateCategories();
            });
    }

    function populateCategories() {
        const uniqueCategories = [...new Set(products.map(p => p.category_name))];
        categoryFilter.innerHTML = '<option value="">Toutes les catégories</option>';
        uniqueCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            categoryFilter.appendChild(option);
        });
    }

    function renderTable() {
        const search = searchInput.value.toLowerCase();
        const cat = categoryFilter.value;
        tableBody.innerHTML = '';
        products.filter(p => {
            return (
                (!cat || p.category_name === cat) &&
                (p.name.toLowerCase().includes(search) || p.model.toLowerCase().includes(search))
            );
        }).forEach(product => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><img src="${product.main_image || '/static/images/no-image.png'}" class="w-12 h-12 object-cover" /></td>
                <td>${product.name}</td>
                <td>${product.category_name}</td>
                <td>${product.current_stock}</td>
                <td>${product.min_stock_level}</td>
                <td>${product.max_stock_level}</td>
                <td>${product.selling_price}</td>
                <td><span class="badge ${product.stock_status === 'low' ? 'badge-warning' : product.stock_status === 'out' ? 'badge-error' : 'badge-success'}">${product.stock_status}</span></td>
                <td><button class="btn btn-xs btn-outline" data-id="${product.id}" data-stock="${product.current_stock}">Ajuster</button></td>
            `;
            tableBody.appendChild(tr);
        });
    }

    tableBody.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' && e.target.dataset.id) {
            adjustProductId.value = e.target.dataset.id;
            newStockInput.value = e.target.dataset.stock;
            adjustModal.classList.remove('hidden');
        }
    });

    cancelAdjust.addEventListener('click', function() {
        adjustModal.classList.add('hidden');
    });

    adjustForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const id = adjustProductId.value;
        const newStock = newStockInput.value;
        axios.put(`/inventory/api/products/${id}/adjust_stock/`, { new_stock: newStock })
            .then(() => {
                adjustModal.classList.add('hidden');
                fetchInventory();
            });
    });

    searchInput.addEventListener('input', renderTable);
    categoryFilter.addEventListener('change', renderTable);

    exportBtn.addEventListener('click', function() {
        window.location.href = '/inventory/export_inventory/';
    });

    fetchInventory();
});
