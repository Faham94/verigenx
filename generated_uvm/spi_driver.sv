class spi_driver extends uvm_driver #(spi_seq_item);

    virtual spi_if vif;

    `uvm_component_utils(spi_driver)

    function new(string name = "spi_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual spi_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("DRV", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "driver_reset" %}
        vif.cb.rst_n <= 0;
        #100;
        vif.cb.rst_n <= 1;
// {% endllm_fill %}

        forever begin
            seq_item_port.get_next_item(req);
            // {% llm_fill "driver_drive_item" %}
        @(posedge vif.clk);
            vif.cb.mosi <= req.mosi;
        #10;
// {% endllm_fill %}
            seq_item_port.item_done();
        end
    endtask

endclass