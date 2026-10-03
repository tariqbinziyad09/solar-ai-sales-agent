import { useEffect, useMemo, useState } from "react";



import {



    Battery,



    Boxes,



    Edit3,



    Plus,



    RefreshCw,



    Search,



    X,



    Zap,



} from "lucide-react";







import api from "../services/api";











const EMPTY_FORM = {



    category: "panel",







    name: "",



    brand: "",



    sku: "",



    description: "",



    price: "",







    wattage: "",



    technology: "",



    efficiency: "",



    warranty_years: "",







    power_kw: "",



    inverter_type: "hybrid",



    phase: "",



    mppt_count: "",







    chemistry: "",



    capacity_kwh: "",



    voltage: "",



    cycle_life: "",



};











function Products() {

    // Frontend RBAC: catalog write controls are Admin-only.

    // Backend RBAC remains the authoritative security layer.

    let currentUser = null;



    try {

        currentUser = JSON.parse(localStorage.getItem("solar_crm_user"));

    } catch {

        currentUser = null;

    }



    const canManageCatalog = currentUser?.role === "admin";



    const [products, setProducts] = useState([]);







    const [loading, setLoading] = useState(true);



    const [saving, setSaving] = useState(false);







    const [error, setError] = useState("");



    const [success, setSuccess] = useState("");







    const [search, setSearch] = useState("");



    const [categoryFilter, setCategoryFilter] = useState("all");







    const [showModal, setShowModal] = useState(false);



    const [editingProduct, setEditingProduct] = useState(null);







    const [form, setForm] = useState(EMPTY_FORM);











    // ========================================================



    // LOAD PRODUCTS



    // ========================================================







    const loadProducts = async () => {



        try {



            setLoading(true);



            setError("");







            const response = await api.get("/products");







            setProducts(response.data);



        } catch (err) {



            console.error(err);







            setError(



                err.response?.data?.detail ||



                "Unable to load product catalog."



            );



        } finally {



            setLoading(false);



        }



    };











    useEffect(() => {



        loadProducts();



    }, []);











    // ========================================================



    // FILTER PRODUCTS



    // ========================================================







    const filteredProducts = useMemo(() => {



        const query = search.trim().toLowerCase();







        return products.filter((product) => {



            const matchesCategory =



                categoryFilter === "all" ||



                product.category === categoryFilter;







            const searchableText = [



                product.name,



                product.brand,



                product.sku,



                product.category,



            ]



                .filter(Boolean)



                .join(" ")



                .toLowerCase();







            const matchesSearch =



                !query ||



                searchableText.includes(query);







            return matchesCategory && matchesSearch;



        });



    }, [products, categoryFilter, search]);











    // ========================================================



    // COUNTS



    // ========================================================







    const counts = useMemo(() => {



        return {



            all: products.length,







            panel: products.filter(



                (item) => item.category === "panel"



            ).length,







            inverter: products.filter(



                (item) => item.category === "inverter"



            ).length,







            battery: products.filter(



                (item) => item.category === "battery"



            ).length,



        };



    }, [products]);











    // ========================================================



    // FORM HELPERS



    // ========================================================







    const updateForm = (event) => {



        const { name, value } = event.target;







        setForm((current) => ({



            ...current,



            [name]: value,



        }));



    };











    const openCreateModal = () => {



        setEditingProduct(null);



        setForm(EMPTY_FORM);







        setError("");



        setSuccess("");







        setShowModal(true);



    };











    const openEditModal = (product) => {



        setEditingProduct(product);







        setForm({



            category: product.category,







            name: product.name || "",



            brand: product.brand || "",



            sku: product.sku || "",



            description: product.description || "",



            price: product.price ?? "",







            wattage: product.wattage ?? "",



            technology: product.technology || "",



            efficiency: product.efficiency ?? "",



            warranty_years: product.warranty_years ?? "",







            power_kw: product.power_kw ?? "",



            inverter_type: product.inverter_type || "hybrid",



            phase: product.phase || "",



            mppt_count: product.mppt_count ?? "",







            chemistry: product.chemistry || "",



            capacity_kwh: product.capacity_kwh ?? "",



            voltage: product.voltage ?? "",



            cycle_life: product.cycle_life ?? "",



        });







        setError("");



        setSuccess("");







        setShowModal(true);



    };











    const closeModal = () => {



        if (saving) {



            return;



        }







        setShowModal(false);



        setEditingProduct(null);



        setForm(EMPTY_FORM);



    };











    // ========================================================



    // VALUE HELPERS



    // ========================================================







    const optionalText = (value) => {



        const clean = String(value ?? "").trim();







        return clean === "" ? null : clean;



    };











    const optionalNumber = (value) => {



        if (



            value === "" ||



            value === null ||



            value === undefined



        ) {



            return null;



        }







        return Number(value);



    };











    // ========================================================



    // CREATE PAYLOAD



    // ========================================================







    const buildCreatePayload = () => {



        const common = {



            name: form.name.trim(),



            brand: optionalText(form.brand),



            sku: optionalText(form.sku),



            description: optionalText(form.description),



            price: optionalNumber(form.price),



        };











        if (form.category === "panel") {



            return {



                ...common,







                wattage: Number(form.wattage),



                technology: optionalText(form.technology),



                efficiency: optionalNumber(form.efficiency),



                warranty_years: optionalNumber(



                    form.warranty_years



                ),



            };



        }











        if (form.category === "inverter") {



            return {



                ...common,







                power_kw: Number(form.power_kw),



                inverter_type: form.inverter_type.trim(),



                phase: optionalText(form.phase),



                mppt_count: optionalNumber(form.mppt_count),



                efficiency: optionalNumber(form.efficiency),



                warranty_years: optionalNumber(



                    form.warranty_years



                ),



            };



        }











        return {



            ...common,







            chemistry: optionalText(form.chemistry),



            capacity_kwh: Number(form.capacity_kwh),



            voltage: optionalNumber(form.voltage),



            cycle_life: optionalNumber(form.cycle_life),



            warranty_years: optionalNumber(



                form.warranty_years



            ),



        };



    };











    // ========================================================



    // UPDATE PAYLOAD



    // ========================================================







    const buildUpdatePayload = () => {



        const common = {



            name: form.name.trim(),



            brand: optionalText(form.brand),



            sku: optionalText(form.sku),



            description: optionalText(form.description),



            price: optionalNumber(form.price),



        };











        if (form.category === "panel") {



            return {



                ...common,







                wattage: Number(form.wattage),



                technology: optionalText(form.technology),



                efficiency: optionalNumber(form.efficiency),



                warranty_years: optionalNumber(



                    form.warranty_years



                ),



            };



        }











        if (form.category === "inverter") {



            return {



                ...common,







                power_kw: Number(form.power_kw),



                inverter_type: form.inverter_type.trim(),



                phase: optionalText(form.phase),



                mppt_count: optionalNumber(form.mppt_count),



                efficiency: optionalNumber(form.efficiency),



                warranty_years: optionalNumber(



                    form.warranty_years



                ),



            };



        }











        return {



            ...common,







            chemistry: optionalText(form.chemistry),



            capacity_kwh: Number(form.capacity_kwh),



            voltage: optionalNumber(form.voltage),



            cycle_life: optionalNumber(form.cycle_life),



            warranty_years: optionalNumber(



                form.warranty_years



            ),



        };



    };











    // ========================================================



    // SAVE PRODUCT



    // ========================================================







    const saveProduct = async (event) => {



        event.preventDefault();







        setSaving(true);



        setError("");



        setSuccess("");







        try {



            if (editingProduct) {



                await api.patch(



                    `/products/${editingProduct.id}`,



                    buildUpdatePayload()



                );







                setSuccess(



                    "Product updated successfully."



                );



            } else {



                const payload = buildCreatePayload();







                const endpointMap = {



                    panel: "/products/panels",



                    inverter: "/products/inverters",



                    battery: "/products/batteries",



                };







                await api.post(



                    endpointMap[form.category],



                    payload



                );







                setSuccess(



                    "Product added successfully."



                );



            }







            setShowModal(false);



            setEditingProduct(null);



            setForm(EMPTY_FORM);







            await loadProducts();







        } catch (err) {



            console.error(err);







            const detail = err.response?.data?.detail;







            if (Array.isArray(detail)) {



                setError(



                    detail



                        .map((item) => item.msg)



                        .join(", ")



                );



            } else {



                setError(



                    detail ||



                    "Unable to save product."



                );



            }







        } finally {



            setSaving(false);



        }



    };











    // ========================================================



    // ACTIVATE / DEACTIVATE



    // ========================================================







    const toggleProductStatus = async (product) => {



        try {



            setError("");



            setSuccess("");







            await api.patch(



                `/products/${product.id}/status`,



                {



                    is_active: !product.is_active,



                }



            );







            setSuccess(



                product.is_active



                    ? `${product.name} deactivated.`



                    : `${product.name} activated.`



            );







            await loadProducts();







        } catch (err) {



            console.error(err);







            setError(



                err.response?.data?.detail ||



                "Unable to change product status."



            );



        }



    };











    // ========================================================



    // FORMATTERS



    // ========================================================







    const formatPrice = (price) => {



        if (



            price === null ||



            price === undefined



        ) {



            return "Not set";



        }







        return `PKR ${Number(price).toLocaleString()}`;



    };











    const categoryName = (category) => {



        const names = {



            panel: "Solar Panel",



            inverter: "Inverter",



            battery: "Battery",



        };







        return names[category] || category;



    };











    const technicalSummary = (product) => {



        if (product.category === "panel") {



            return product.wattage



                ? `${product.wattage}W`



                : "—";



        }







        if (product.category === "inverter") {



            return product.power_kw



                ? `${product.power_kw} kW`



                : "—";



        }







        if (product.category === "battery") {



            return product.capacity_kwh



                ? `${product.capacity_kwh} kWh`



                : "—";



        }







        return "—";



    };











    // ========================================================



    // UI



    // ========================================================







    return (



        <div className="products-page">







            <div className="products-header catalog-hero">



                <div>



                    <p className="page-eyebrow">



                        INVENTORY MANAGEMENT



                    </p>







                    <h1>Product Catalog</h1>







                    <p>



                        Manage solar panels, inverters and



                        batteries used by your sales system.



                    </p>



                </div>







                {canManageCatalog && (









                    <button









                        className="primary-action-btn"









                        onClick={openCreateModal}









                    >









                        <Plus size={18} />









                        Add Product









                    </button>









                )}



            </div>











            {error && (



                <div className="catalog-message error">



                    {error}



                </div>



            )}











            {success && (



                <div className="catalog-message success">



                    {success}



                </div>



            )}











            <div className="catalog-stats catalog-kpi-grid">







                <div className="catalog-stat-card">



                    <Boxes size={20} />







                    <div>



                        <span>Total Products</span>



                        <strong>{counts.all}</strong>



                    </div>



                </div>











                <div className="catalog-stat-card">



                    <Zap size={20} />







                    <div>



                        <span>Solar Panels</span>



                        <strong>{counts.panel}</strong>



                    </div>



                </div>











                <div className="catalog-stat-card">



                    <Zap size={20} />







                    <div>



                        <span>Inverters</span>



                        <strong>{counts.inverter}</strong>



                    </div>



                </div>











                <div className="catalog-stat-card">



                    <Battery size={20} />







                    <div>



                        <span>Batteries</span>



                        <strong>{counts.battery}</strong>



                    </div>



                </div>







            </div>











            <div className="catalog-toolbar catalog-toolbar-polished">







                <div className="catalog-search">



                    <Search size={18} />







                    <input



                        type="text"



                        placeholder="Search name, brand or SKU..."



                        value={search}



                        onChange={(event) =>



                            setSearch(event.target.value)



                        }



                    />



                </div>











                <div className="catalog-filters">







                    {[



                        ["all", "All"],



                        ["panel", "Panels"],



                        ["inverter", "Inverters"],



                        ["battery", "Batteries"],



                    ].map(([value, label]) => (



                        <button



                            key={value}



                            className={



                                categoryFilter === value



                                    ? "catalog-filter active"



                                    : "catalog-filter"



                            }



                            onClick={() =>



                                setCategoryFilter(value)



                            }



                        >



                            {label}



                        </button>



                    ))}







                </div>











                <button



                    className="catalog-refresh-btn"



                    onClick={loadProducts}



                    title="Refresh catalog"



                >



                    <RefreshCw size={18} />



                </button>







            </div>











            <div className="catalog-table-card catalog-data-card">







                {loading ? (



                    <div className="catalog-empty">



                        Loading product catalog...



                    </div>



                ) : filteredProducts.length === 0 ? (



                    <div className="catalog-empty">



                        No products found.



                    </div>



                ) : (



                    <div className="catalog-table-wrapper">







                        <table className="catalog-table">







                            <thead>



                                <tr>



                                    <th>Product</th>



                                    <th>Category</th>



                                    <th>Brand</th>



                                    <th>Specification</th>



                                    <th>Price</th>



                                    <th>Status</th>



                                    <th>{canManageCatalog ? "Actions" : "Access"}</th>



                                </tr>



                            </thead>







                            <tbody>







                                {filteredProducts.map(



                                    (product) => (



                                        <tr key={product.id}>







                                            <td>



                                                <div className="product-name-cell">



                                                    <strong>



                                                        {product.name}



                                                    </strong>







                                                    <span>



                                                        {product.sku ||



                                                            `Product #${product.id}`}



                                                    </span>



                                                </div>



                                            </td>











                                            <td>



                                                <span



                                                    className={`category-badge ${product.category}`}



                                                >



                                                    {categoryName(



                                                        product.category



                                                    )}



                                                </span>



                                            </td>











                                            <td>



                                                {product.brand || "—"}



                                            </td>











                                            <td>



                                                {technicalSummary(



                                                    product



                                                )}



                                            </td>











                                            <td className="catalog-price">



                                                {formatPrice(



                                                    product.price



                                                )}



                                            </td>











                                            <td>



                                                <span



                                                    className={



                                                        product.is_active



                                                            ? "product-status active"



                                                            : "product-status inactive"



                                                    }



                                                >



                                                    {product.is_active



                                                        ? "Active"



                                                        : "Inactive"}



                                                </span>



                                            </td>











                                            <td>



                                                {canManageCatalog ? (

                                                    <div className="catalog-actions">

                                                        <button

                                                            className="catalog-edit-btn"

                                                            onClick={() =>

                                                                openEditModal(product)

                                                            }

                                                        >

                                                            <Edit3 size={15} />

                                                            Edit

                                                        </button>



                                                        <button

                                                            className={

                                                                product.is_active

                                                                    ? "catalog-status-btn deactivate"

                                                                    : "catalog-status-btn activate"

                                                            }

                                                            onClick={() =>

                                                                toggleProductStatus(product)

                                                            }

                                                        >

                                                            {product.is_active

                                                                ? "Deactivate"

                                                                : "Activate"}

                                                        </button>

                                                    </div>

                                                ) : (

                                                    <span className="catalog-readonly">

                                                        Read only

                                                    </span>

                                                )}



                                            </td>







                                        </tr>



                                    )



                                )}







                            </tbody>







                        </table>







                    </div>



                )}







            </div>











            {/* =================================================



                ADD / EDIT PRODUCT MODAL



            ================================================= */}







            {canManageCatalog && showModal && (



                <div className="catalog-modal-backdrop">







                    <div className="catalog-modal catalog-modal-polished">







                        <div className="catalog-modal-header">







                            <div>



                                <p className="page-eyebrow">



                                    {editingProduct



                                        ? "EDIT CATALOG ITEM"



                                        : "NEW CATALOG ITEM"}



                                </p>







                                <h2>



                                    {editingProduct



                                        ? "Edit Product"



                                        : "Add Product"}



                                </h2>



                            </div>











                            <button



                                className="modal-close-btn"



                                onClick={closeModal}



                            >



                                <X size={20} />



                            </button>







                        </div>











                        <form



                            onSubmit={saveProduct}



                            className="catalog-form"



                        >







                            {!editingProduct && (



                                <div className="catalog-form-group full">







                                    <label>Product Category</label>







                                    <select



                                        name="category"



                                        value={form.category}



                                        onChange={updateForm}



                                    >



                                        <option value="panel">



                                            Solar Panel



                                        </option>







                                        <option value="inverter">



                                            Inverter



                                        </option>







                                        <option value="battery">



                                            Battery



                                        </option>



                                    </select>







                                </div>



                            )}











                            <div className="catalog-form-grid">







                                <div className="catalog-form-group">



                                    <label>Product Name *</label>







                                    <input



                                        name="name"



                                        value={form.name}



                                        onChange={updateForm}



                                        required



                                        minLength={2}



                                    />



                                </div>











                                <div className="catalog-form-group">



                                    <label>Brand</label>







                                    <input



                                        name="brand"



                                        value={form.brand}



                                        onChange={updateForm}



                                    />



                                </div>











                                <div className="catalog-form-group">



                                    <label>SKU</label>







                                    <input



                                        name="sku"



                                        value={form.sku}



                                        onChange={updateForm}



                                    />



                                </div>











                                <div className="catalog-form-group">



                                    <label>Price (PKR)</label>







                                    <input



                                        type="number"



                                        name="price"



                                        value={form.price}



                                        onChange={updateForm}



                                        min="0"



                                        step="0.01"



                                    />



                                </div>











                                {/* PANEL */}







                                {form.category === "panel" && (



                                    <>



                                        <div className="catalog-form-group">



                                            <label>Wattage *</label>







                                            <input



                                                type="number"



                                                name="wattage"



                                                value={form.wattage}



                                                onChange={updateForm}



                                                min="1"



                                                required



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Technology</label>







                                            <input



                                                name="technology"



                                                value={form.technology}



                                                onChange={updateForm}



                                                placeholder="N-Type TOPCon"



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Efficiency %</label>







                                            <input



                                                type="number"



                                                name="efficiency"



                                                value={form.efficiency}



                                                onChange={updateForm}



                                                min="0.01"



                                                max="100"



                                                step="0.01"



                                            />



                                        </div>



                                    </>



                                )}











                                {/* INVERTER */}







                                {form.category === "inverter" && (



                                    <>



                                        <div className="catalog-form-group">



                                            <label>Power (kW) *</label>







                                            <input



                                                type="number"



                                                name="power_kw"



                                                value={form.power_kw}



                                                onChange={updateForm}



                                                min="0.01"



                                                step="0.01"



                                                required



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Inverter Type *</label>







                                            <select



                                                name="inverter_type"



                                                value={form.inverter_type}



                                                onChange={updateForm}



                                                required



                                            >



                                                <option value="hybrid">



                                                    Hybrid



                                                </option>







                                                <option value="on-grid">



                                                    On-Grid



                                                </option>







                                                <option value="off-grid">



                                                    Off-Grid



                                                </option>



                                            </select>



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Phase</label>







                                            <select



                                                name="phase"



                                                value={form.phase}



                                                onChange={updateForm}



                                            >



                                                <option value="">



                                                    Not specified



                                                </option>







                                                <option value="single-phase">



                                                    Single Phase



                                                </option>







                                                <option value="three-phase">



                                                    Three Phase



                                                </option>



                                            </select>



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>MPPT Count</label>







                                            <input



                                                type="number"



                                                name="mppt_count"



                                                value={form.mppt_count}



                                                onChange={updateForm}



                                                min="1"



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Efficiency %</label>







                                            <input



                                                type="number"



                                                name="efficiency"



                                                value={form.efficiency}



                                                onChange={updateForm}



                                                min="0.01"



                                                max="100"



                                                step="0.01"



                                            />



                                        </div>



                                    </>



                                )}











                                {/* BATTERY */}







                                {form.category === "battery" && (



                                    <>



                                        <div className="catalog-form-group">



                                            <label>



                                                Capacity (kWh) *



                                            </label>







                                            <input



                                                type="number"



                                                name="capacity_kwh"



                                                value={form.capacity_kwh}



                                                onChange={updateForm}



                                                min="0.01"



                                                step="0.01"



                                                required



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Chemistry</label>







                                            <input



                                                name="chemistry"



                                                value={form.chemistry}



                                                onChange={updateForm}



                                                placeholder="LiFePO4"



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Voltage</label>







                                            <input



                                                type="number"



                                                name="voltage"



                                                value={form.voltage}



                                                onChange={updateForm}



                                                min="0.01"



                                                step="0.01"



                                            />



                                        </div>











                                        <div className="catalog-form-group">



                                            <label>Cycle Life</label>







                                            <input



                                                type="number"



                                                name="cycle_life"



                                                value={form.cycle_life}



                                                onChange={updateForm}



                                                min="1"



                                            />



                                        </div>



                                    </>



                                )}











                                <div className="catalog-form-group">



                                    <label>Warranty Years</label>







                                    <input



                                        type="number"



                                        name="warranty_years"



                                        value={form.warranty_years}



                                        onChange={updateForm}



                                        min="0"



                                    />



                                </div>











                                <div className="catalog-form-group full">



                                    <label>Description</label>







                                    <textarea



                                        name="description"



                                        value={form.description}



                                        onChange={updateForm}



                                        rows={4}



                                    />



                                </div>







                            </div>











                            <div className="catalog-modal-actions">







                                <button



                                    type="button"



                                    className="secondary-action-btn"



                                    onClick={closeModal}



                                    disabled={saving}



                                >



                                    Cancel



                                </button>











                                <button



                                    type="submit"



                                    className="primary-action-btn"



                                    disabled={saving}



                                >



                                    {saving



                                        ? "Saving..."



                                        : editingProduct



                                            ? "Save Changes"



                                            : "Add Product"}



                                </button>







                            </div>







                        </form>







                    </div>







                </div>



            )}







        </div>



    );



}











export default Products;