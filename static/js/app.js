const body = document.body;
const page = body.dataset.page;

function setupThemeToggle() {
    const themeToggle = document.getElementById("themeToggle");
    const savedTheme = localStorage.getItem("tripora-theme");
    if (savedTheme === "dark") {
        body.classList.add("dark-mode");
    }
    if (themeToggle) {
        themeToggle.textContent = body.classList.contains("dark-mode") ? "☀️" : "🌙";
        themeToggle.addEventListener("click", () => {
            body.classList.toggle("dark-mode");
            const dark = body.classList.contains("dark-mode");
            localStorage.setItem("tripora-theme", dark ? "dark" : "light");
            themeToggle.textContent = dark ? "☀️" : "🌙";
        });
    }
}

function setupLoader() {
    if (page !== "loader") return;
    const progressFill = document.getElementById("progressFill");
    const progressCount = document.getElementById("progressCount");
    if (!progressFill || !progressCount) return;

    let progress = 0;
    const timer = setInterval(() => {
        progress += 2;
        progressFill.style.width = `${progress}%`;
        progressCount.textContent = `${progress}`;
        if (progress >= 100) {
            clearInterval(timer);
            window.location.href = "/login/";
        }
    }, 40);
}

function readRecentSearches() {
    try {
        return JSON.parse(localStorage.getItem("tripora-recent-searches") || "[]");
    } catch (error) {
        return [];
    }
}

function saveRecentSearch(form) {
    const source = form.querySelector('input[name="source"]')?.value?.trim();
    const destination = form.querySelector('input[name="destination"]')?.value?.trim();
    const date = form.querySelector('input[name="date"]')?.value?.trim();
    if (!source || !destination || !date) return;

    const next = [{ source, destination, date }, ...readRecentSearches()]
        .filter((item, index, array) => index === array.findIndex((entry) => (
            entry.source === item.source &&
            entry.destination === item.destination &&
            entry.date === item.date
        )))
        .slice(0, 5);

    localStorage.setItem("tripora-recent-searches", JSON.stringify(next));
}

function renderRecentSearches() {
    const wrapper = document.getElementById("recentSearches");
    if (!wrapper) return;
    const recent = readRecentSearches();
    wrapper.innerHTML = "";
    if (!recent.length) {
        wrapper.innerHTML = '<span class="muted-copy">Recent searches will appear here after your first search.</span>';
        return;
    }

    recent.forEach((item) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "recent-chip";
        chip.textContent = `${item.source} → ${item.destination} • ${item.date}`;
        chip.addEventListener("click", () => {
            window.location.href = `/search/?source=${encodeURIComponent(item.source)}&destination=${encodeURIComponent(item.destination)}&date=${encodeURIComponent(item.date)}`;
        });
        wrapper.appendChild(chip);
    });
}

function setupRecentSearches() {
    document.querySelectorAll("form[data-recent-search='true']").forEach((form) => {
        form.addEventListener("submit", () => saveRecentSearch(form));
    });
    renderRecentSearches();
}

function setupAuthValidation() {
    const authForms = document.querySelectorAll("form[data-auth-form]");
    if (!authForms.length) return;

    const usernamePattern = /^[A-Za-z]{5,}$/;
    const fullNamePattern = /^[A-Za-z ]{3,}$/;
    const strongPasswordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$/;

    authForms.forEach((form) => {
        const mode = form.dataset.authForm;
        const formMessage = form.querySelector("[data-auth-form-error]");

        const setError = (field, message = "") => {
            const errorEl = form.querySelector(`[data-auth-error="${field}"]`);
            if (errorEl) {
                errorEl.textContent = message;
            }
        };

        const validate = () => {
            let valid = true;
            let firstError = "";

            ["full_name", "username", "email", "password", "confirm_password"].forEach((field) => setError(field, ""));
            if (formMessage) {
                formMessage.textContent = "";
            }

            const username = form.querySelector('input[name="username"]')?.value?.trim() || "";
            const password = form.querySelector('input[name="password"]')?.value || "";

            if (!usernamePattern.test(username)) {
                setError("username", "Username must be at least 5 letters and contain only letters.");
                valid = false;
                firstError ||= "Please enter a valid username.";
            }

            if (!strongPasswordPattern.test(password)) {
                setError("password", "Password must be 8+ chars with uppercase, lowercase, and special character.");
                valid = false;
                firstError ||= "Please enter a stronger password.";
            }

            if (mode === "signup") {
                const fullName = form.querySelector('input[name="full_name"]')?.value?.trim() || "";
                const email = form.querySelector('input[name="email"]')?.value?.trim() || "";
                const confirmPassword = form.querySelector('input[name="confirm_password"]')?.value || "";
                const emailField = form.querySelector('input[name="email"]');

                if (!fullNamePattern.test(fullName)) {
                    setError("full_name", "Enter a valid full name using letters and spaces.");
                    valid = false;
                    firstError ||= "Please enter your full name.";
                }

                if (!emailField?.checkValidity() || !email) {
                    setError("email", "Please enter a valid email address.");
                    valid = false;
                    firstError ||= "Please enter a valid email.";
                }

                if (password !== confirmPassword) {
                    setError("confirm_password", "Passwords do not match.");
                    valid = false;
                    firstError ||= "Passwords do not match.";
                }
            }

            if (formMessage && !valid) {
                formMessage.textContent = firstError;
            }

            return valid;
        };

        form.querySelectorAll("input").forEach((input) => {
            input.addEventListener("input", validate);
            input.addEventListener("change", validate);
        });

        form.addEventListener("submit", (event) => {
            if (!validate()) {
                event.preventDefault();
            }
        });
    });
}

function setupDashboardSearchControls() {
    const searchSection = document.getElementById("search-tabs");
    if (!searchSection) return;

    const form = document.getElementById("searchHubForm") || searchSection.querySelector("form");
    const sourceInput = form?.querySelector('input[name="source"]');
    const destinationInput = form?.querySelector('input[name="destination"]');
    const dateInput = form?.querySelector('input[name="date"]');
    const maxPriceInput = form?.querySelector('input[name="max_price"]');
    const modeInput = document.getElementById("searchMode");
    const transportButtons = searchSection.querySelectorAll(".transport-toggle");
    const submitButton = document.getElementById("searchSubmitButton");
    const formError = document.getElementById("searchFormErrors");
    const swapButton = document.getElementById("swapRouteButton");
    const fieldErrors = {
        source: document.querySelector('[data-error-for="source"]'),
        destination: document.querySelector('[data-error-for="destination"]'),
        date: document.querySelector('[data-error-for="date"]'),
        budget: document.querySelector('[data-error-for="budget"]'),
    };

    if (dateInput && !dateInput.value) {
        const nextWeek = new Date();
        nextWeek.setDate(nextWeek.getDate() + 7);
        dateInput.value = nextWeek.toISOString().split("T")[0];
    }

    if (dateInput) {
        dateInput.min = new Date().toISOString().split("T")[0];
    }

    function syncTransportSelection(selectedMode = "Flight") {
        transportButtons.forEach((button) => {
            const isActive = (button.dataset.mode || "") === selectedMode;
            button.classList.toggle("active", isActive);
            button.setAttribute("aria-pressed", isActive ? "true" : "false");
        });

        if (modeInput) {
            modeInput.value = selectedMode;
        }
    }

    function setFieldError(name, message = "") {
        if (fieldErrors[name]) {
            fieldErrors[name].textContent = message;
        }
    }

    function validateSearchForm() {
        const source = sourceInput?.value?.trim() || "";
        const destination = destinationInput?.value?.trim() || "";
        const budgetValue = maxPriceInput?.value?.trim() || "";
        const selectedDate = dateInput?.value || "";
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        let isValid = true;
        let firstError = "";

        Object.keys(fieldErrors).forEach((key) => setFieldError(key, ""));
        if (formError) {
            formError.textContent = "";
        }

        if (!source) {
            setFieldError("source", "Departure city is required.");
            isValid = false;
            firstError ||= "Please enter your departure city.";
        }

        if (!destination) {
            setFieldError("destination", "Destination city is required.");
            isValid = false;
            firstError ||= "Please enter your destination city.";
        }

        if (source && destination && source.toLowerCase() === destination.toLowerCase()) {
            setFieldError("destination", "Destination must be different from departure.");
            isValid = false;
            firstError ||= "From and To cannot be the same.";
        }

        if (!selectedDate) {
            setFieldError("date", "Departure date is required.");
            isValid = false;
            firstError ||= "Please choose a departure date.";
        } else {
            const travelDate = new Date(selectedDate);
            travelDate.setHours(0, 0, 0, 0);
            if (travelDate < today) {
                setFieldError("date", "Departure date cannot be in the past.");
                isValid = false;
                firstError ||= "Departure date cannot be in the past.";
            }
        }

        if (!budgetValue) {
            setFieldError("budget", "Budget cap is required.");
            isValid = false;
            firstError ||= "Please enter your budget cap.";
        } else {
            const budget = Number(budgetValue);
            if (!Number.isFinite(budget)) {
                setFieldError("budget", "Budget must be a valid number.");
                isValid = false;
                firstError ||= "Budget must be a valid number.";
            } else if (budget <= 0) {
                setFieldError("budget", "Budget must be greater than 0.");
                isValid = false;
                firstError ||= "Budget must be greater than 0.";
            } else if (budget < 500) {
                setFieldError("budget", "Budget cannot be lower than 500.");
                isValid = false;
                firstError ||= "Budget cannot be lower than 500.";
            } else if (budget > 1000000) {
                setFieldError("budget", "Budget cannot exceed 1000000.");
                isValid = false;
                firstError ||= "Budget cannot exceed 1000000.";
            }
        }

        if (submitButton) {
            submitButton.disabled = !isValid;
        }

        if (!isValid && formError) {
            formError.textContent = firstError;
        }

        return isValid;
    }

    swapButton?.addEventListener("click", () => {
        const currentSource = sourceInput?.value || "";
        sourceInput.value = destinationInput?.value || "";
        destinationInput.value = currentSource;
        validateSearchForm();
    });

    transportButtons.forEach((button) => {
        button.addEventListener("click", () => {
            syncTransportSelection(button.dataset.mode || "Flight");
        });
    });

    [sourceInput, destinationInput, dateInput, maxPriceInput].forEach((input) => {
        input?.addEventListener("input", validateSearchForm);
        input?.addEventListener("change", validateSearchForm);
    });

    form?.addEventListener("submit", (event) => {
        if (!validateSearchForm()) {
            event.preventDefault();
            window.alert(formError?.textContent || "Please correct the highlighted fields before searching.");
        }
    });

    syncTransportSelection(modeInput?.value || "Flight");
    validateSearchForm();
}

function setupCardFilters() {
    const filterChips = document.querySelectorAll(".filter-chip");
    if (!filterChips.length) return;

    filterChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const group = chip.dataset.filterGroup;
            const filter = chip.dataset.filter;
            const groupChips = document.querySelectorAll(`.filter-chip[data-filter-group="${group}"]`);
            const target = document.querySelector(`[data-filter-target="${group}"]`);
            if (!target) return;

            groupChips.forEach((item) => item.classList.remove("active"));
            chip.classList.add("active");

            target.querySelectorAll("[data-mode]").forEach((card) => {
                const shouldShow = filter === "all" || card.dataset.mode === filter;
                card.style.display = shouldShow ? "" : "none";
            });
        });
    });
}

function setupOfferButtons() {
    document.querySelectorAll(".copy-offer-button").forEach((button) => {
        button.addEventListener("click", async () => {
            const code = button.dataset.offerCode;
            if (!code) return;

            try {
                await navigator.clipboard.writeText(code);
                const original = button.textContent;
                button.textContent = "Offer Applied";
                setTimeout(() => {
                    button.textContent = original;
                }, 1200);
            } catch (error) {
                button.textContent = code;
            }
        });
    });
}

function setupPlanner() {
    const plannerForm = document.getElementById("plannerForm");
    const plannerResult = document.getElementById("plannerResult");
    const plannerPanel = document.getElementById("planner");
    if (!plannerForm || !plannerResult || !plannerPanel) return;

    plannerForm.addEventListener("submit", () => {
        plannerResult.innerHTML = "Finding the best available trip for your plan...";
    });
}

function setupItineraryPlanner() {
    const form = document.getElementById("itineraryForm");
    const output = document.getElementById("itineraryOutput");
    if (!form || !output) return;

    const renderItinerary = (payload) => {
        const days = payload.itinerary || [];
        output.innerHTML = days.map((item) => `
            <article class="itinerary-day-card glass-panel">
                <div class="itinerary-day-badge">Day ${item.day}</div>
                <div class="itinerary-day-header">
                    <span class="itinerary-icon">${item.icon}</span>
                    <div>
                        <h3>${item.title}</h3>
                    </div>
                </div>
                <div class="itinerary-place-list">
                    ${item.places.map((place) => `
                        <div class="itinerary-place-item">
                            <strong>${place.name}</strong>
                            <p>${place.description}</p>
                        </div>
                    `).join("")}
                </div>
            </article>
        `).join("");
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const params = new URLSearchParams({
            days: form.elements.days.value,
            budget: form.elements.budget.value,
            travel_type: form.elements.travel_type.value,
        });

        output.innerHTML = '<div class="empty-state"><h3>Generating itinerary...</h3><p>Please wait while Tripora builds your plan.</p></div>';

        try {
            const response = await fetch(`/api/itinerary/?${params.toString()}`);
            const payload = await response.json();
            renderItinerary(payload);
        } catch (error) {
            output.innerHTML = '<div class="empty-state"><h3>Unable to generate plan</h3><p>Please try again in a moment.</p></div>';
        }
    });
}

function buildBotReply(message) {
    const text = message.toLowerCase();
    const unrelatedTopics = ["math", "movie", "weather", "politics", "code", "programming", "recipe", "football"];

    if (unrelatedTopics.some((item) => text.includes(item))) {
        return "I can help only with travel-related questions such as destinations, budgets, transport options, stays, or itinerary ideas.";
    }
    if (text.includes("beach")) {
        return "For a beach vibe, Goa and Kochi are the strongest fits. Goa is better for nightlife, while Kochi works beautifully for a slower scenic break.";
    }
    if (text.includes("peace") || text.includes("sleep") || text.includes("calm") || text.includes("relax")) {
        return "For a peaceful stay, Kochi and Shimla are the best fits. Kochi is better for backwaters and slow scenery, while Shimla is better for cool weather and quiet mountain views.";
    }
    if (text.includes("dance") || text.includes("party") || text.includes("nightlife")) {
        return "For nightlife and energy, Goa is the easiest recommendation. If you want something more premium and city-focused, Dubai is the stronger luxury nightlife option.";
    }
    if (text.includes("budget")) {
        return "If you want value, Jaipur, Shimla, and Varanasi are great starting points. They keep fares lower while still offering strong culture and sightseeing.";
    }
    if (text.includes("family")) {
        return "For family trips, Jaipur and Kochi are easy wins with comfortable pacing, sightseeing variety, and broad appeal across age groups.";
    }
    if (text.includes("weekend")) {
        return "For a quick weekend escape, Goa or Jaipur are easiest to recommend because they deliver a lot without needing a long itinerary.";
    }
    if (text.includes("culture") || text.includes("spiritual") || text.includes("history")) {
        return "For culture-rich travel, Jaipur and Varanasi are strong picks. Jaipur gives you forts and heritage, while Varanasi is better for spiritual and riverside experiences.";
    }
    if (text.includes("luxury")) {
        return "For a luxury-style trip, Dubai is the best option in Tripora right now. It offers premium stays, skyline views, and a polished big-city travel experience.";
    }
    return "I can help with beach trips, budget ideas, family routes, weekend plans, or cultural destinations. Try asking in one of those styles.";
}

function setupChatbot() {
    const form = document.getElementById("chatForm");
    const input = document.getElementById("chatInput");
    const windowEl = document.getElementById("chatWindow");
    const typingIndicator = document.getElementById("typingIndicator");
    if (!form || !input || !windowEl) return;

    const sendMessage = (message) => {
        if (!message) return;

        const userBubble = document.createElement("div");
        userBubble.className = "chat-bubble user";
        userBubble.textContent = message;
        windowEl.appendChild(userBubble);

        if (typingIndicator) {
            typingIndicator.hidden = false;
        }

        setTimeout(() => {
            if (typingIndicator) {
                typingIndicator.hidden = true;
            }

            const botBubble = document.createElement("div");
            botBubble.className = "chat-bubble bot";
            botBubble.textContent = buildBotReply(message);
            windowEl.appendChild(botBubble);
            windowEl.scrollTop = windowEl.scrollHeight;
        }, 700);

        windowEl.scrollTop = windowEl.scrollHeight;
    };

    document.querySelectorAll("[data-chat-prompt]").forEach((button) => {
        button.addEventListener("click", () => {
            const prompt = button.dataset.chatPrompt || "";
            const autoSend = button.classList.contains("assistant-shortcut");
            if (autoSend) {
                sendMessage(prompt);
                input.value = "";
            } else {
                input.value = prompt;
                input.focus();
            }
        });
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const message = input.value.trim();
        if (!message) return;
        sendMessage(message);
        input.value = "";
    });
}

function setupFareCalculator() {
    const bookingForm = document.querySelector(".booking-form");
    const travelerNameInput = document.getElementById("travelerNameInput");
    const travelerNameError = document.getElementById("travelerNameError");
    const passengersInput = document.getElementById("passengersInput");
    const passengersError = document.getElementById("passengersError");
    const baseFare = document.getElementById("baseFare");
    const gstFare = document.getElementById("gstFare");
    const feeFare = document.getElementById("feeFare");
    const totalFare = document.getElementById("totalFare");
    const submitButton = document.getElementById("bookingSubmitButton");
    const splitCount = document.getElementById("splitCount");
    const splitAmount = document.getElementById("splitAmount");
    if (!bookingForm || !travelerNameInput || !passengersInput || !baseFare || !gstFare || !feeFare || !totalFare || !splitCount || !splitAmount || !submitButton) return;

    const baseFareValue = Number(baseFare.dataset.baseFare || 0);
    const convenienceFee = 150;

    const formatCurrency = (value) => `₹ ${value.toFixed(2)}`;

    const validateName = () => {
        const value = travelerNameInput.value.trim();
        const valid = /^[A-Za-z ]+$/.test(value) && value.replace(/\s/g, "").length >= 3;
        travelerNameError.textContent = valid || !value ? "" : "Enter at least 3 letters using only letters and spaces.";
        return valid;
    };

    const validatePassengers = () => {
        const value = Number(passengersInput.value || 0);
        const valid = Number.isInteger(value) && value >= 1 && value <= 20;
        passengersError.textContent = valid ? "" : "Passengers must be between 1 and 20.";
        return valid;
    };

    const recalculate = () => {
        const passengers = Math.min(20, Math.max(1, Number(passengersInput.value || 1)));
        const splitBy = Math.max(1, Number(splitCount.value || 1));
        const baseTotal = baseFareValue * passengers;
        const gstTotal = baseTotal * 0.05;
        const total = baseTotal + gstTotal + convenienceFee;
        const perPerson = total / splitBy;

        baseFare.textContent = formatCurrency(baseTotal);
        gstFare.textContent = formatCurrency(gstTotal);
        feeFare.textContent = formatCurrency(convenienceFee);
        totalFare.textContent = formatCurrency(total);
        splitAmount.textContent = formatCurrency(perPerson);

        const formValid = validateName() && validatePassengers();
        submitButton.disabled = !formValid;
        submitButton.classList.toggle("is-disabled", !formValid);
    };

    travelerNameInput.addEventListener("input", recalculate);
    passengersInput.addEventListener("input", recalculate);
    splitCount.addEventListener("input", recalculate);
    bookingForm.addEventListener("submit", (event) => {
        const formValid = validateName() && validatePassengers();
        if (!formValid) {
            event.preventDefault();
        }
    });
    recalculate();
}

function setupPaymentTabs() {
    const paymentTabs = document.querySelectorAll(".payment-tab");
    if (!paymentTabs.length) return;
    const paymentPanels = document.querySelectorAll("[data-payment-panel]");
    const cardNumberInput = document.querySelector('[data-payment-panel="Card"] input[placeholder="1234 5678 9012 3456"]');
    const expiryInput = document.querySelector('[data-payment-panel="Card"] input[placeholder="MM/YY"]');
    const cvvInput = document.querySelector('[data-payment-panel="Card"] input[placeholder="123"]');

    const applyPaymentConfig = (method) => {
        paymentPanels.forEach((panel) => {
            const isActive = panel.dataset.paymentPanel === method;
            panel.classList.toggle("is-visible", isActive);
            panel.hidden = !isActive;
            panel.querySelectorAll("input").forEach((input) => {
                input.required = isActive;
                if (!isActive) input.value = "";
            });
        });
    };

    paymentTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            paymentTabs.forEach((otherTab) => otherTab.classList.remove("active"));
            tab.classList.add("active");
            const input = tab.querySelector("input");
            if (input) {
                input.checked = true;
                applyPaymentConfig(input.value);
            }
        });
    });

    const checked = document.querySelector('.payment-tab input:checked');
    applyPaymentConfig(checked?.value || "Card");

    if (cardNumberInput) {
        cardNumberInput.addEventListener("input", () => {
            const digits = cardNumberInput.value.replace(/\D/g, "").slice(0, 16);
            cardNumberInput.value = digits.replace(/(.{4})/g, "$1 ").trim();
        });
    }

    if (expiryInput) {
        expiryInput.addEventListener("input", () => {
            const digits = expiryInput.value.replace(/\D/g, "").slice(0, 4);
            expiryInput.value = digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
        });
    }

    if (cvvInput) {
        cvvInput.addEventListener("input", () => {
            cvvInput.value = cvvInput.value.replace(/\D/g, "").slice(0, 3);
        });
    }
}

function setupInvoicePrint() {
    const button = document.getElementById("printInvoiceButton");
    if (!button) return;
    button.addEventListener("click", () => window.print());
}

setupThemeToggle();
setupLoader();
setupRecentSearches();
setupAuthValidation();
setupDashboardSearchControls();
setupCardFilters();
setupOfferButtons();
setupPlanner();
setupItineraryPlanner();
setupChatbot();
setupFareCalculator();
setupPaymentTabs();
setupInvoicePrint();
