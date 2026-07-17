class i2c_driver extends uvm_driver #(i2c_seq_item);

    virtual i2c_if vif;

    `uvm_component_utils(i2c_driver)

    function new(string name = "i2c_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual i2c_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("DRV", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "driver_reset" %}
        vif.rst_n <= 0;
        #100;
        vif.rst_n <= 1;
// {% endllm_fill %}

        forever begin
            seq_item_port.get_next_item(req);
            // {% llm_fill "driver_drive_item" %}
        @(posedge vif.clk);
            vif.scl <= req.scl;
            vif.sda <= req.sda;
        #10;
// {% endllm_fill %}
            seq_item_port.item_done();
        end
    endtask

endclass