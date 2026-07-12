// Reference model base class for injection
class fifo_ref_model extends uvm_object;
    `uvm_object_utils(fifo_ref_model)

    function new(string name = "fifo_ref_model");
        super.new(name);
    endfunction

    // {% llm_fill "ref_model_predict" %}
    virtual function void predict(fifo_seq_item item, ref fifo_seq_item expected);
        expected = fifo_seq_item::type_id::create("expected");
        // Predict next expected outputs based on inputs
    endfunction
// {% endllm_fill %}
endclass


class fifo_scoreboard extends uvm_scoreboard;

    uvm_analysis_imp #(fifo_seq_item, fifo_scoreboard) item_export;
    fifo_ref_model ref_model;

    `uvm_component_utils(fifo_scoreboard)

    function new(string name = "fifo_scoreboard", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        item_export = new("item_export", this);
        
        // Configuration DB retrieval of injectable reference model
        if (!uvm_config_db#(fifo_ref_model)::get(this, "", "ref_model", ref_model)) begin
            `uvm_info("SB", "No reference model injected. Creating default reference model.", UVM_MEDIUM)
            ref_model = fifo_ref_model::type_id::create("ref_model");
        end
    endfunction

    virtual function void write(fifo_seq_item item);
        // {% llm_fill "scoreboard_write" %}
        fifo_seq_item expected;
        ref_model.predict(item, expected);
        // Compare item (actual) against expected
        `uvm_info("SB", $sformatf("Verified transaction: %s", item.convert2string()), UVM_MEDIUM)
// {% endllm_fill %}
    endfunction

endclass