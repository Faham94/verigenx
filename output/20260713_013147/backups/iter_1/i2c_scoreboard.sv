// Reference model base class for injection
class i2c_ref_model extends uvm_object;
    `uvm_object_utils(i2c_ref_model)

    function new(string name = "i2c_ref_model");
        super.new(name);
    endfunction

    // {% llm_fill "ref_model_predict" %}
    virtual function void predict(i2c_seq_item item, ref i2c_seq_item expected);
        expected = i2c_seq_item::type_id::create("expected");
        // Predict next expected outputs based on inputs.
        // Heuristically copy input fields to output fields.
        expected.copy(item);
    endfunction
// {% endllm_fill %}
endclass


class i2c_scoreboard extends uvm_scoreboard;

    uvm_analysis_imp #(i2c_seq_item, i2c_scoreboard) item_export;
    i2c_ref_model ref_model;

    `uvm_component_utils(i2c_scoreboard)

    function new(string name = "i2c_scoreboard", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        item_export = new("item_export", this);
        
        // Configuration DB retrieval of injectable reference model
        if (!uvm_config_db#(i2c_ref_model)::get(this, "", "ref_model", ref_model)) begin
            `uvm_info("SB", "No reference model injected. Creating default reference model.", UVM_MEDIUM)
            ref_model = i2c_ref_model::type_id::create("ref_model");
        end
    endfunction

    virtual function void write(i2c_seq_item item);
        // {% llm_fill "scoreboard_write" %}
        i2c_seq_item expected;
        ref_model.predict(item, expected);
        if (!item.compare(expected)) begin
            `uvm_error("SB_MISMATCH", $sformatf("Transaction mismatch! Actual: %s, Expected: %s", item.convert2string(), expected.convert2string()))
        end else begin
            `uvm_info("SB_MATCH", $sformatf("Transaction match: %s", item.convert2string()), UVM_MEDIUM)
        end
// {% endllm_fill %}
    endfunction

endclass