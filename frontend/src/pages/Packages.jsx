import { useEffect, useMemo, useState } from "react";



import {



    Edit3,



    PackageOpen,



    Plus,



    RefreshCw,



    Search,



    Trash2,



    X,



} from "lucide-react";







import api from "../services/api";



import "./Packages.css";











const EMPTY_FORM = {



    name: "",



    description: "",



    system_size_kw: "",



    system_type: "hybrid",



    package_price: "",



    items: [],



};











function Packages() {

    // Frontend RBAC: package write controls are Admin-only.

    // Managers and Executives can inspect package data but cannot mutate it.

    let currentUser = null;



    try {

        currentUser = JSON.parse(localStorage.getItem("solar_crm_user"));

    } catch {

        currentUser = null;

    }



    const canManageCatalog = currentUser?.role === "admin";



    const [packages, setPackages] = useState([]);



    const [products, setProducts] = useState([]);







    const [loading, setLoading] = useState(true);



    const [saving, setSaving] = useState(false);







    const [error, setError] = useState("");



    const [success, setSuccess] = useState("");







    const [search, setSearch] = useState("");



    const [typeFilter, setTypeFilter] = useState("all");







    const [showModal, setShowModal] = useState(false);



    const [editingPackage, setEditingPackage] = useState(null);







    const [form, setForm] = useState(EMPTY_FORM);











    // ========================================================



    // LOAD PACKAGES + PRODUCTS



    // ========================================================







    const loadData = async () => {



        try {



            setLoading(true);



            setError("");







            const [packagesResponse, productsResponse] =



                await Promise.all([



                    api.get("/packages/admin/all"),



                    api.get("/products?active_only=true"),



                ]);







            setPackages(packagesResponse.data);



            setProducts(productsResponse.data);







        } catch (err) {



            console.error(err);







            setError(



                err.response?.data?.detail ||



                "Unable to load package management data."



            );



        } finally {



            setLoading(false);



        }



    };











    useEffect(() => {



        loadData();



    }, []);











    // ========================================================



    // FILTERING



    // ========================================================







    const filteredPackages = useMemo(() => {



        const query = search.trim().toLowerCase();







        return packages.filter((solarPackage) => {



            const matchesType =



                typeFilter === "all" ||



                solarPackage.system_type === typeFilter;







            const searchable = [



                solarPackage.name,



                solarPackage.description,



                solarPackage.system_type,



                solarPackage.system_size_kw,



            ]



                .filter(



                    (value) =>



                        value !== null &&



                        value !== undefined



                )



                .join(" ")



                .toLowerCase();







            const matchesSearch =



                !query ||



                searchable.includes(query);







            return matchesType && matchesSearch;



        });



    }, [packages, search, typeFilter]);











    // ========================================================



    // STATS



    // ========================================================







    const stats = useMemo(() => {



        return {



            total: packages.length,







            active: packages.filter(



                (item) => item.is_active



            ).length,







            hybrid: packages.filter(



                (item) =>



                    item.system_type === "hybrid"



            ).length,







            inactive: packages.filter(



                (item) => !item.is_active



            ).length,



        };



    }, [packages]);











    // ========================================================



    // FORM



    // ========================================================







    const updateForm = (event) => {



        const { name, value } = event.target;







        setForm((current) => ({



            ...current,



            [name]: value,



        }));



    };











    const openCreateModal = () => {



        setEditingPackage(null);



        setForm(EMPTY_FORM);



        setError("");



        setSuccess("");



        setShowModal(true);



    };











    const openEditModal = (solarPackage) => {



        setEditingPackage(solarPackage);







        setForm({



            name: solarPackage.name || "",



            description:



                solarPackage.description || "",



            system_size_kw:



                solarPackage.system_size_kw ?? "",



            system_type:



                solarPackage.system_type || "hybrid",



            package_price:



                solarPackage.package_price ?? "",







            items: solarPackage.items.map(



                (item) => ({



                    product_id:



                        String(item.product_id),







                    quantity:



                        String(item.quantity),



                })



            ),



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



        setEditingPackage(null);



        setForm(EMPTY_FORM);



    };











    // ========================================================



    // PACKAGE ITEMS



    // ========================================================







    const addProductRow = () => {



        setForm((current) => ({



            ...current,







            items: [



                ...current.items,



                {



                    product_id: "",



                    quantity: "1",



                },



            ],



        }));



    };











    const updatePackageItem = (



        index,



        field,



        value



    ) => {



        setForm((current) => ({



            ...current,







            items: current.items.map(



                (item, itemIndex) =>



                    itemIndex === index



                        ? {



                            ...item,



                            [field]: value,



                        }



                        : item



            ),



        }));



    };











    const removePackageItem = (index) => {



        setForm((current) => ({



            ...current,







            items: current.items.filter(



                (_, itemIndex) =>



                    itemIndex !== index



            ),



        }));



    };











    // ========================================================



    // PAYLOAD



    // ========================================================







    const buildPayload = () => ({



        name: form.name.trim(),







        description:



            form.description.trim() || null,







        system_size_kw:



            Number(form.system_size_kw),







        system_type:



            form.system_type,







        package_price:



            Number(form.package_price),







        items: form.items.map((item) => ({



            product_id:



                Number(item.product_id),







            quantity:



                Number(item.quantity),



        })),



    });











    // ========================================================



    // SAVE PACKAGE



    // ========================================================







    const savePackage = async (event) => {



        event.preventDefault();







        if (form.items.length === 0) {



            setError(



                "Please add at least one product to the package."



            );







            return;



        }











        const productIds = form.items.map(



            (item) => item.product_id



        );











        if (productIds.some((id) => !id)) {



            setError(



                "Please select a product for every package item."



            );







            return;



        }











        if (



            new Set(productIds).size !==



            productIds.length



        ) {



            setError(



                "The same product cannot be added twice."



            );







            return;



        }











        try {



            setSaving(true);



            setError("");



            setSuccess("");







            const payload = buildPayload();











            if (editingPackage) {



                await api.patch(



                    `/packages/${editingPackage.id}`,



                    payload



                );







                setSuccess(



                    "Solar package updated successfully."



                );







            } else {



                await api.post(



                    "/packages",



                    payload



                );







                setSuccess(



                    "Solar package created successfully."



                );



            }











            setShowModal(false);



            setEditingPackage(null);



            setForm(EMPTY_FORM);







            await loadData();







        } catch (err) {



            console.error(err);







            const detail =



                err.response?.data?.detail;







            if (Array.isArray(detail)) {



                setError(



                    detail



                        .map((item) => item.msg)



                        .join(", ")



                );



            } else {



                setError(



                    detail ||



                    "Unable to save solar package."



                );



            }







        } finally {



            setSaving(false);



        }



    };











    // ========================================================



    // STATUS



    // ========================================================







    const togglePackageStatus = async (



        solarPackage



    ) => {



        try {



            setError("");



            setSuccess("");







            await api.patch(



                `/packages/${solarPackage.id}/status`,



                {



                    is_active:



                        !solarPackage.is_active,



                }



            );







            setSuccess(



                solarPackage.is_active



                    ? `${solarPackage.name} deactivated.`



                    : `${solarPackage.name} activated.`



            );







            await loadData();







        } catch (err) {



            console.error(err);







            setError(



                err.response?.data?.detail ||



                "Unable to change package status."



            );



        }



    };











    // ========================================================



    // HELPERS



    // ========================================================







    const formatPrice = (price) => {



        return `PKR ${Number(



            price || 0



        ).toLocaleString()}`;



    };











    const formatSystemType = (type) => {



        const labels = {



            hybrid: "Hybrid",



            "on-grid": "On-Grid",



            "off-grid": "Off-Grid",



        };







        return labels[type] || type;



    };











    const productLabel = (product) => {



        let specification = "";







        if (



            product.category === "panel" &&



            product.wattage



        ) {



            specification =



                ` • ${product.wattage}W`;



        }







        if (



            product.category === "inverter" &&



            product.power_kw



        ) {



            specification =



                ` • ${product.power_kw}kW`;



        }







        if (



            product.category === "battery" &&



            product.capacity_kwh



        ) {



            specification =



                ` • ${product.capacity_kwh}kWh`;



        }







        return (



            `${product.name}` +



            specification



        );



    };











    // ========================================================



    // UI



    // ========================================================







    return (



        <div className="packages-page">







            <div className="packages-header package-hero">







                <div>



                    <p className="packages-eyebrow">



                        PACKAGE MANAGEMENT



                    </p>







                    <h1>Solar Packages</h1>







                    <p>



                        Build and manage packages used by



                        the AI recommendation engine.



                    </p>



                </div>











                {canManageCatalog && (













                    <button













                        className="package-primary-btn"













                        onClick={openCreateModal}













                    >













                        <Plus size={18} />













                        Add Package













                    </button>













                )}







            </div>











            {error && (



                <div className="package-message error">



                    {error}



                </div>



            )}











            {success && (



                <div className="package-message success">



                    {success}



                </div>



            )}











            {/* STATS */}







            <div className="package-stats package-kpi-grid">







                <div className="package-stat">



                    <PackageOpen size={20} />







                    <div>



                        <span>Total Packages</span>



                        <strong>{stats.total}</strong>



                    </div>



                </div>











                <div className="package-stat">



                    <PackageOpen size={20} />







                    <div>



                        <span>Active</span>



                        <strong>{stats.active}</strong>



                    </div>



                </div>











                <div className="package-stat">



                    <PackageOpen size={20} />







                    <div>



                        <span>Hybrid</span>



                        <strong>{stats.hybrid}</strong>



                    </div>



                </div>











                <div className="package-stat">



                    <PackageOpen size={20} />







                    <div>



                        <span>Inactive</span>



                        <strong>{stats.inactive}</strong>



                    </div>



                </div>







            </div>











            {/* TOOLBAR */}







            <div className="package-toolbar package-toolbar-polished">







                <div className="package-search">







                    <Search size={18} />







                    <input



                        type="text"



                        placeholder="Search packages..."



                        value={search}



                        onChange={(event) =>



                            setSearch(



                                event.target.value



                            )



                        }



                    />







                </div>











                <div className="package-filters">







                    {[



                        ["all", "All"],



                        ["hybrid", "Hybrid"],



                        ["on-grid", "On-Grid"],



                        ["off-grid", "Off-Grid"],



                    ].map(([value, label]) => (







                        <button



                            key={value}



                            className={



                                typeFilter === value



                                    ? "package-filter active"



                                    : "package-filter"



                            }



                            onClick={() =>



                                setTypeFilter(value)



                            }



                        >



                            {label}



                        </button>







                    ))}







                </div>











                <button



                    className="package-refresh"



                    onClick={loadData}



                >



                    <RefreshCw size={18} />



                </button>







            </div>











            {/* TABLE */}







            <div className="package-table-card package-data-card">







                {loading ? (







                    <div className="package-empty">



                        Loading solar packages...



                    </div>







                ) : filteredPackages.length === 0 ? (







                    <div className="package-empty">



                        No solar packages found.



                    </div>







                ) : (







                    <div className="package-table-wrapper">







                        <table className="package-table">







                            <thead>



                                <tr>



                                    <th>Package</th>



                                    <th>System</th>



                                    <th>Products</th>



                                    <th>Price</th>



                                    <th>Status</th>



                                    <th>{canManageCatalog ? "Actions" : "Access"}</th>



                                </tr>



                            </thead>











                            <tbody>







                                {filteredPackages.map(



                                    (solarPackage) => (







                                        <tr



                                            key={



                                                solarPackage.id



                                            }



                                        >







                                            <td>



                                                <div className="package-name">



                                                    <strong>



                                                        {



                                                            solarPackage.name



                                                        }



                                                    </strong>







                                                    <span>



                                                        Package #



                                                        {



                                                            solarPackage.id



                                                        }



                                                    </span>



                                                </div>



                                            </td>











                                            <td>



                                                <strong>



                                                    {



                                                        solarPackage.system_size_kw



                                                    }{" "}



                                                    kW



                                                </strong>







                                                <span className="package-system-type">



                                                    {formatSystemType(



                                                        solarPackage.system_type



                                                    )}



                                                </span>



                                            </td>











                                            <td>



                                                <div className="package-product-summary">







                                                    {solarPackage.items.map(



                                                        (item) => (



                                                            <span



                                                                key={



                                                                    item.product_id



                                                                }



                                                            >



                                                                {



                                                                    item.name



                                                                }{" "}



                                                                ×{" "}



                                                                {



                                                                    item.quantity



                                                                }



                                                            </span>



                                                        )



                                                    )}







                                                </div>



                                            </td>











                                            <td className="package-price">



                                                {formatPrice(



                                                    solarPackage.package_price



                                                )}



                                            </td>











                                            <td>



                                                <span



                                                    className={



                                                        solarPackage.is_active



                                                            ? "package-status active"



                                                            : "package-status inactive"



                                                    }



                                                >



                                                    {solarPackage.is_active



                                                        ? "Active"



                                                        : "Inactive"}



                                                </span>



                                            </td>











                                            <td>



                                                {canManageCatalog ? (

                                                    <div className="package-actions">

                                                        <button

                                                            className="package-edit"

                                                            onClick={() =>

                                                                openEditModal(solarPackage)

                                                            }

                                                        >

                                                            <Edit3 size={15} />

                                                            Edit

                                                        </button>



                                                        <button

                                                            className={

                                                                solarPackage.is_active

                                                                    ? "package-status-btn deactivate"

                                                                    : "package-status-btn activate"

                                                            }

                                                            onClick={() =>

                                                                togglePackageStatus(solarPackage)

                                                            }

                                                        >

                                                            {solarPackage.is_active

                                                                ? "Deactivate"

                                                                : "Activate"}

                                                        </button>

                                                    </div>

                                                ) : (

                                                    <span className="package-readonly">

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



                CREATE / EDIT MODAL



            ================================================= */}







            {canManageCatalog && showModal && (







                <div className="package-modal-backdrop">







                    <div className="package-modal package-modal-polished">







                        <div className="package-modal-header">







                            <div>



                                <p className="packages-eyebrow">



                                    {editingPackage



                                        ? "EDIT PACKAGE"



                                        : "NEW PACKAGE"}



                                </p>







                                <h2>



                                    {editingPackage



                                        ? "Edit Solar Package"



                                        : "Create Solar Package"}



                                </h2>



                            </div>











                            <button



                                className="package-close"



                                onClick={closeModal}



                            >



                                <X size={20} />



                            </button>







                        </div>











                        <form



                            onSubmit={savePackage}



                            className="package-form"



                        >







                            <div className="package-form-grid">







                                <div className="package-field">



                                    <label>



                                        Package Name *



                                    </label>







                                    <input



                                        name="name"



                                        value={form.name}



                                        onChange={updateForm}



                                        required



                                        minLength={2}



                                        placeholder="8kW Premium Hybrid"



                                    />



                                </div>











                                <div className="package-field">



                                    <label>



                                        System Size (kW) *



                                    </label>







                                    <input



                                        type="number"



                                        name="system_size_kw"



                                        value={



                                            form.system_size_kw



                                        }



                                        onChange={updateForm}



                                        required



                                        min="0.1"



                                        step="0.1"



                                    />



                                </div>











                                <div className="package-field">



                                    <label>



                                        System Type *



                                    </label>







                                    <select



                                        name="system_type"



                                        value={



                                            form.system_type



                                        }



                                        onChange={updateForm}



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











                                <div className="package-field">



                                    <label>



                                        Package Price (PKR) *



                                    </label>







                                    <input



                                        type="number"



                                        name="package_price"



                                        value={



                                            form.package_price



                                        }



                                        onChange={updateForm}



                                        required



                                        min="0"



                                        step="0.01"



                                    />



                                </div>











                                <div className="package-field full">



                                    <label>Description</label>







                                    <textarea



                                        name="description"



                                        value={



                                            form.description



                                        }



                                        onChange={updateForm}



                                        rows={3}



                                        placeholder="Package description..."



                                    />



                                </div>







                            </div>











                            {/* PACKAGE PRODUCTS */}







                            <div className="package-items-section">







                                <div className="package-items-header">







                                    <div>



                                        <h3>



                                            Package Products



                                        </h3>







                                        <p>



                                            Select products and



                                            their quantities.



                                        </p>



                                    </div>











                                    <button



                                        type="button"



                                        className="add-package-item"



                                        onClick={addProductRow}



                                    >



                                        <Plus size={16} />



                                        Add Product



                                    </button>







                                </div>











                                {form.items.length === 0 ? (







                                    <div className="no-package-items">



                                        No products added yet.



                                    </div>







                                ) : (







                                    <div className="package-item-list">







                                        {form.items.map(



                                            (item, index) => (







                                                <div



                                                    className="package-item-row"



                                                    key={index}



                                                >







                                                    <select



                                                        value={



                                                            item.product_id



                                                        }



                                                        onChange={(



                                                            event



                                                        ) =>



                                                            updatePackageItem(



                                                                index,



                                                                "product_id",



                                                                event



                                                                    .target



                                                                    .value



                                                            )



                                                        }



                                                        required



                                                    >



                                                        <option value="">



                                                            Select product



                                                        </option>







                                                        {products.map(



                                                            (



                                                                product



                                                            ) => (







                                                                <option



                                                                    key={



                                                                        product.id



                                                                    }



                                                                    value={



                                                                        product.id



                                                                    }



                                                                >



                                                                    {productLabel(



                                                                        product



                                                                    )}



                                                                </option>







                                                            )



                                                        )}







                                                    </select>











                                                    <input



                                                        type="number"



                                                        min="1"



                                                        value={



                                                            item.quantity



                                                        }



                                                        onChange={(



                                                            event



                                                        ) =>



                                                            updatePackageItem(



                                                                index,



                                                                "quantity",



                                                                event



                                                                    .target



                                                                    .value



                                                            )



                                                        }



                                                        required



                                                        placeholder="Qty"



                                                    />











                                                    <button



                                                        type="button"



                                                        className="remove-package-item"



                                                        onClick={() =>



                                                            removePackageItem(



                                                                index



                                                            )



                                                        }



                                                    >



                                                        <Trash2



                                                            size={



                                                                17



                                                            }



                                                        />



                                                    </button>







                                                </div>



                                            )



                                        )}







                                    </div>



                                )}







                            </div>











                            <div className="package-modal-actions">







                                <button



                                    type="button"



                                    className="package-secondary-btn"



                                    onClick={closeModal}



                                    disabled={saving}



                                >



                                    Cancel



                                </button>











                                <button



                                    type="submit"



                                    className="package-primary-btn"



                                    disabled={saving}



                                >



                                    {saving



                                        ? "Saving..."



                                        : editingPackage



                                            ? "Save Changes"



                                            : "Create Package"}



                                </button>







                            </div>







                        </form>







                    </div>







                </div>



            )}







        </div>



    );



}











export default Packages;