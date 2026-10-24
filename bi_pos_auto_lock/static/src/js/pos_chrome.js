/** @odoo-module */
  
import { Chrome } from "@point_of_sale/app/pos_app";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks"; 
import { Component, onWillStart } from "@odoo/owl";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";


patch(Chrome.prototype, {
	setup() {
		super.setup();
		this.popup = useService("popup");
		this.pos = usePos();

		this.lock_timer_screen = false;
		this.remove_screen = false;

		onWillStart(this.start);
	},
	
	async start() {
		var self = this;
		if (this.pos.config.enable_lock) {
			var loack_screen_interval = function (time) {
				time = time || self.pos.config.lock_timer * 1000;
				if (time) {
					self.pos.timer_out = setTimeout(function () {
						self.lock_timer_screen = true
						$(".pos").before('<div class="lock_screen"><h3>Click to unlock...</h3></div>');
					}, time);
				}
			};
		}
		if (this.pos.config.enable_lock && this.pos.config.lock_timer) {
			$(document).on("click", async function (event) {
				if (self.pos.config.enable_lock && self.pos.config.lock_timer) {
					clearTimeout(self.pos.timer_out);
					loack_screen_interval();
					if ($(".lock_screen").length > 0) {
						if(!this.remove_screen){
							$(".lock_screen").remove();
						}else{
							this.remove_screen = false
						}
						const current = Component.current;
						if (self.pos.config.module_pos_hr) {
							const list = self.pos.employees.map((employee) => {
								if (employee.name == self.pos.get_cashier().name) {
									return {
										id: employee.id,
										item: employee,
										label: employee.name,
										isSelected: true,
									};
								} else {
									return {
										id: employee.id,
										item: employee,
										label: employee.name,
										isSelected: false,
									};
								}
							});

							const { confirmed, payload: selectedCashier } = await self.popup.add(SelectionPopup, {
								title: _t("Change Cashier"),
								list: list,
								
							});

							if (!confirmed) {
								if(this.lock_timer_screen){
									this.remove_screen = true
									event.preventDefault()
									$(".pos").before('<div class="lock_screen"><h3>Click to unlock...</h3></div>');
								}
								return false;
							}
							if (!selectedCashier.pin) {
								self.pos.set_cashier(selectedCashier);
								this.lock_timer_screen = false;
								return selectedCashier;
							} else {
								return self.pin_number(selectedCashier);
							}
						}else{
							this.lock_timer_screen = false;
						}
					}
				}
			});
			loack_screen_interval();
		}
	},

	async pin_number(employee) {
		const { confirmed, payload: inputPin } = await this.popup.add(NumberPopup, {
			isPassword: true,
			title: _t("Password ?")
		});

		if (!confirmed) {
			if(this.lock_timer_screen){
				$(".pos").before('<div class="lock_screen"><h3>Click to unlock...</h3></div>');
			}
			return false;
		}
		if (employee.pin === Sha1.hash(inputPin)) {
			this.pos.set_cashier(employee);
			this.lock_timer_screen = false;
			return employee;
		} else {
			alert("Password Is Not Correct.")
			if(this.lock_timer_screen){
				$(".pos").before('<div class="lock_screen"><h3>Click to unlock...</h3></div>');
			}
			return false;
		}
	}

});
