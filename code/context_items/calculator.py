#!/usr/bin/env python3
'''
When given a list of documents, finds common metadata that is common amongst
them, and gives links back.

'''

CALC_SCRIPT = """<form name="Calc" id="Calc">
    <table border="4">
      <tr>
        <td><input type="text" name="Input" size="16" value="%s" /><br /></td>
      </tr>

      <tr>
        <td><input type="button" name="one" value=" 1 " onclick=
        "Calc.Input.value += '1'" /> <input type="button" name="two" value=" 2 " onclick=
        "Calc.Input.value += '2'" /> <input type="button" name="three" value=" 3 "
        onclick="Calc.Input.value += '3'" /> <input type="button" name="plus" value=" + "
        onclick="Calc.Input.value += ' + '" /><br />
        <input type="button" name="four" value=" 4 " onclick="Calc.Input.value += '4'" />
        <input type="button" name="five" value=" 5 " onclick="Calc.Input.value += '5'" />
        <input type="button" name="six" value=" 6 " onclick="Calc.Input.value += '6'" />
        <input type="button" name="minus" value=" - " onclick=
        "Calc.Input.value += ' - '" /><br />
        <input type="button" name="seven" value=" 7 " onclick=
        "Calc.Input.value += '7'" /> <input type="button" name="eight" value=" 8 "
        onclick="Calc.Input.value += '8'" /> <input type="button" name="nine" value=" 9 "
        onclick="Calc.Input.value += '9'" /> <input type="button" name="times" value=
        " x " onclick="Calc.Input.value += ' * '" /><br />
        <input type="button" name="clear" value=" c " onclick="Calc.Input.value = ''" />
        <input type="button" name="zero" value=" 0 " onclick="Calc.Input.value += '0'" />
        <input type="button" name="DoIt" value=" = " onclick=
        "Calc.Input.value = eval(Calc.Input.value)" /> <input type="button" name="div"
        value=" / " onclick="Calc.Input.value += ' / '" /><br /></td>
      </tr>
    </table>
  </form>
  
  <script type='text/javascript'>Calc.Input.value = eval(Calc.Input.value);</script>
  """




TITLE = "Calculator"

def get_item(query, doc_id_rank_map, database):
	''' Checks to see if the value is calculatable, if so, calculates and 
	returns a calculator.
	'''
	
	acceptable_chars = ['0','1','2','3','4','5','6','7','8','9','-',' ','+','*','/','(',')','.']
	
	for char in query:
		if char not in acceptable_chars:
			return ""

	return CALC_SCRIPT % (query)
