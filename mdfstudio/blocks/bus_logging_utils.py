import numpy as np

from .conversion_utils import from_dict
from .utils import as_non_byte_sized_signed_int, MdfException


def extract_signal(signal, payload, raw=False, ignore_value2text_conversion=True):
    vals = payload

    big_endian = False if signal.is_little_endian else True
    signed = signal.is_signed
    is_float = signal.is_float

    start_bit = signal.get_startbit(bit_numbering=1)

    if big_endian:
        start_byte = start_bit // 8
        bit_count = signal.size

        pos = start_bit % 8 + 1

        over = bit_count % 8

        if pos >= over:
            bit_offset = (pos - over) % 8
        else:
            bit_offset = pos + 8 - over
    else:
        start_byte, bit_offset = divmod(start_bit, 8)

    bit_count = signal.size

    if is_float:
        if bit_offset:
            raise MdfException(
                f"Cannot extract float signal '{signal}' because it is not byte aligned"
            )
        if bit_count not in (16, 32, 64):
            raise MdfException(
                f"Cannot extract float signal '{signal}' because it does not have a standard byte size"
            )

    if big_endian:
        byte_pos = start_byte + 1
        start_pos = start_bit
        bits = bit_count

        while True:
            pos = start_pos % 8 + 1
            if pos < bits:
                byte_pos += 1
                bits -= pos
                start_pos = 7
            else:
                break

        if byte_pos > vals.shape[1]:
            raise MdfException(
                f'Could not extract signal "{signal.name}" with start '
                f"bit {start_bit} and bit count {signal.size} "
                f"from the payload with shape {vals.shape}"
            )
    else:
        if start_bit + bit_count > vals.shape[1] * 8:
            raise MdfException(
                f'Could not extract signal "{signal.name}" with start '
                f"bit {start_bit} and bit count {signal.size} "
                f"from the payload with shape {vals.shape}"
            )

    byte_size, r = divmod(bit_offset + bit_count, 8)
    if r:
        byte_size += 1

    if byte_size in (1, 2, 4, 8):
        extra_bytes = 0
    else:
        extra_bytes = 4 - (byte_size % 4)

    std_size = byte_size + extra_bytes

    # prepend or append extra bytes columns
    # to get a standard size number of bytes

    if extra_bytes:
        if big_endian:

            vals = np.column_stack(
                [
                    vals[:, start_byte : start_byte + byte_size],
                    np.zeros(len(vals), dtype=f"<({extra_bytes},)u1"),
                ]
            )

            if std_size > 8:
                fmt = f"({std_size},)u1"
            elif is_float:
                fmt = f">f{std_size}"
            else:
                fmt = f">u{std_size}"

            try:
                vals = vals.view(fmt).ravel()
            except:
                vals = np.frombuffer(vals.tobytes(), dtype=fmt)

            if std_size <= 8 and not is_float:
                vals = vals >> (extra_bytes * 8 + bit_offset)
                vals &= (2 ** bit_count) - 1

        else:
            vals = np.column_stack(
                [
                    vals[:, start_byte : start_byte + byte_size],
                    np.zeros(len(vals), dtype=f"<({extra_bytes},)u1"),
                ]
            )

            if std_size > 8:
                fmt = f"({std_size},)u1"
            elif is_float:
                fmt = f"<f{std_size}"
            else:
                fmt = f"<u{std_size}"

            try:
                vals = vals.view(fmt).ravel()
            except:
                vals = np.frombuffer(vals.tobytes(), dtype=fmt)

            if std_size <= 8 and not is_float:
                vals = vals >> bit_offset
                vals &= (2 ** bit_count) - 1

    else:
        if big_endian:
            if std_size > 8:
                fmt = f"({std_size},)u1"
            elif is_float:
                fmt = f">f{std_size}"
            else:
                fmt = f">u{std_size}"

            try:
                vals = vals[:, start_byte : start_byte + byte_size].view(fmt).ravel()
            except:
                vals = np.frombuffer(
                    vals[:, start_byte : start_byte + byte_size].tobytes(),
                    dtype=fmt,
                )

            if std_size <= 8 and not is_float:
                vals = vals >> bit_offset
                vals &= (2 ** bit_count) - 1
        else:
            if std_size > 8:
                fmt = f"({std_size},)u1"
            elif is_float:
                fmt = f"<f{std_size}"
            else:
                fmt = f"<u{std_size}"

            try:
                vals = vals[:, start_byte : start_byte + byte_size].view(fmt).ravel()
            except:
                vals = np.frombuffer(
                    vals[:, start_byte : start_byte + byte_size].tobytes(),
                    dtype=fmt,
                )

            if std_size <= 8 and not is_float:
                vals = vals >> bit_offset
                vals &= (2 ** bit_count) - 1

    if signed and not is_float:
        vals = as_non_byte_sized_signed_int(vals, bit_count)

    if not raw:
        a, b = float(signal.factor), float(signal.offset)

        if signal.values and not ignore_value2text_conversion:

            conv = {}
            for i, (val, text) in enumerate(signal.values.items()):
                conv[f"upper_{i}"] = val
                conv[f"lower_{i}"] = val
                conv[f"text_{i}"] = text

            conv["default"] = from_dict({"a": a, "b": b})

            conv = from_dict(conv)
            vals = conv.convert(vals)

        else:

            if (a, b) != (1, 0):
                vals = vals * a
                if b:
                    vals += b

    return vals


def extract_can_signal(signal, payload, raw=False, ignore_value2text_conversion=True):
    return extract_signal(signal, payload, raw, ignore_value2text_conversion)


def extract_lin_signal(signal, payload, raw=False, ignore_value2text_conversion=True):
    return extract_signal(signal, payload, raw, ignore_value2text_conversion)


def extract_mux(
    payload,
    message,
    message_id,
    bus,
    t,
    muxer=None,
    muxer_values=None,
    original_message_id=None,
    raw=False,
    include_message_name=False,
    ignore_value2text_conversion=True,
):
    """extract multiplexed CAN signals from the raw payload

    Parameters
    ----------
    payload : np.ndarray
        raw CAN payload as numpy array
    message : canmatrix.Frame
        CAN message description parsed by canmatrix
    message_id : int
        message id
    original_message_id : int
        original message id
    bus : int
        bus channel number
    t : np.ndarray
        timestamps for the raw payload
    muxer (None): str
        name of the parent multiplexor signal
    muxer_values (None): np.ndarray
        multiplexor signal values
    ignore_value2text_conversion (True): bool
        ignore value to text conversions

        .. versionadded:: 5.23.0


    Returns
    -------
    extracted_signal : dict
        each value in the dict is a list of signals that share the same
        multiplexors

    """

    if muxer is None:
        if message.is_multiplexed:
            for sig in message:
                if sig.multiplex == "Multiplexor" and sig.muxer_for_signal is None:
                    multiplexor_name = sig.name
                    break
            for sig in message:
                if (
                    sig.multiplex not in (None, "Multiplexor")
                    and sig.muxer_for_signal is None
                ):
                    sig.muxer_for_signal = multiplexor_name
                    sig.mux_val_min = sig.mux_val_max = int(sig.multiplex)
                    sig.mux_val_grp.insert(0, (int(sig.multiplex), int(sig.multiplex)))

    extracted_signals = {}

    if message.size > payload.shape[1] or message.size == 0:
        return extracted_signals

    pairs = {}
    for signal in message:
        if signal.muxer_for_signal == muxer:
            try:
                entry = signal.mux_val_min, signal.mux_val_max
            except:
                entry = tuple(signal.mux_val_grp[0]) if signal.mux_val_grp else (0, 0)
            pair_signals = pairs.setdefault(entry, [])
            pair_signals.append(signal)

    for pair, pair_signals in pairs.items():
        entry = bus, message_id, original_message_id, muxer, *pair

        extracted_signals[entry] = signals = {}

        if muxer_values is not None:
            min_, max_ = pair
            idx = np.argwhere((min_ <= muxer_values) & (muxer_values <= max_)).ravel()
            payload_ = payload[idx]
            t_ = t[idx]
        else:
            t_ = t
            payload_ = payload

        for sig in pair_signals:
            samples = extract_signal(sig, payload_, raw, ignore_value2text_conversion)
            if len(samples) == 0 and len(t_):
                continue

            max_val = np.full(len(samples), float(sig.calc_max()))

            if include_message_name:
                sig_name = f"{message.name}.{sig.name}"
            else:
                sig_name = sig.name

            try:
                signals[sig_name] = {
                    "name": sig_name,
                    "comment": sig.comment or "",
                    "unit": sig.unit or "",
                    "samples": samples,
                    "t": t_,
                    "invalidation_bits": (
                        np.isclose(samples, max_val)
                        if len(samples.shape) == 1
                        else np.zeros(len(samples), dtype=bool)
                    ),
                }
            except:
                print(message, sig)
                print(samples, set(samples), samples.dtype, samples.shape)
                print(max_val, max_val.dtype, max_val.shape)
                raise

            if sig.multiplex == "Multiplexor":
                extracted_signals.update(
                    extract_mux(
                        payload_,
                        message,
                        message_id,
                        bus,
                        t_,
                        muxer=sig.name,
                        muxer_values=samples,
                        original_message_id=original_message_id,
                        ignore_value2text_conversion=ignore_value2text_conversion,
                    )
                )

    return extracted_signals
